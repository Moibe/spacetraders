"""Tests de la sesion: persistencia del token y deteccion del reset semanal."""

from __future__ import annotations

import json

import pytest

from spacetraders.client import ApiClient
from spacetraders.errors import ConfigError, ServerResetError
from spacetraders.ratelimit import RateLimiter
from spacetraders.session import AgentCredentials, Session, TokenStore

from .conftest import RespuestaFalsa, SesionFalsa

TEMPORADA_ACTUAL = "2026-08-16"
TEMPORADA_VIEJA = "2026-08-09"

AGENTE = {
    "symbol": "TEST_AGENT",
    "headquarters": "X1-AA11-A1",
    "credits": 175000,
    "startingFaction": "COSMIC",
    "shipCount": 2,
}

CONTRATO = {
    "id": "contrato-1",
    "factionSymbol": "COSMIC",
    "type": "PROCUREMENT",
    "accepted": False,
    "fulfilled": False,
    "expiration": "2026-08-22T00:00:00.000Z",
    "terms": {
        "deadline": "2026-08-22T00:00:00.000Z",
        "payment": {"onAccepted": 1000, "onFulfilled": 10000},
        "deliver": [
            {
                "tradeSymbol": "IRON_ORE",
                "destinationSymbol": "X1-AA11-B2",
                "unitsRequired": 100,
                "unitsFulfilled": 0,
            }
        ],
    },
}


def status(reset_date: str = TEMPORADA_ACTUAL) -> RespuestaFalsa:
    return RespuestaFalsa(
        200,
        {
            "status": "online",
            "version": "v2.3.0",
            "resetDate": reset_date,
            "serverResets": {"next": "2026-08-23T13:00:00.000Z", "frequency": "weekly"},
        },
    )


def registro_ok(token: str = "token-nuevo") -> RespuestaFalsa:
    return RespuestaFalsa(
        201,
        {
            "data": {
                "token": token,
                "agent": AGENTE,
                "contract": CONTRATO,
                "faction": {"symbol": "COSMIC", "name": "Cosmic Engineers", "traits": []},
                "ships": [],
            }
        },
    )


def sesion_de_prueba(settings, respuestas) -> tuple[Session, SesionFalsa]:
    http = SesionFalsa(respuestas)
    cliente = ApiClient(
        settings,
        session=http,
        limiter=RateLimiter(rate_per_second=1e6, burst=1000),
        sleep=lambda _s: None,
    )
    return Session(settings, client=cliente), http


def guardar_credenciales(settings, *, reset_date: str, symbol: str = "TEST_AGENT") -> None:
    TokenStore(settings.token_file).save(
        AgentCredentials(
            agent_symbol=symbol,
            faction="COSMIC",
            token="token-guardado",
            reset_date=reset_date,
            created_at="2026-08-16T00:00:00+00:00",
        )
    )


# ------------------------------------------------------------------- TokenStore


def test_el_store_hace_ida_y_vuelta(tmp_path):
    store = TokenStore(tmp_path / "sub" / "agent.json")
    credenciales = AgentCredentials(
        agent_symbol="A", faction="COSMIC", token="t", reset_date="2026-08-16", created_at="x"
    )
    store.save(credenciales)

    assert store.load() == credenciales
    assert store.path.exists()  # crea el directorio padre solo


def test_el_store_ignora_un_archivo_corrupto(tmp_path):
    ruta = tmp_path / "agent.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert TokenStore(ruta).load() is None


def test_el_store_ignora_un_json_con_campos_de_mas(tmp_path):
    """Un formato viejo no debe romper el arranque; se ignora y se registra de nuevo."""
    ruta = tmp_path / "agent.json"
    ruta.write_text(json.dumps({"token": "solo-token"}), encoding="utf-8")
    assert TokenStore(ruta).load() is None


def test_clear_borra_sin_quejarse_si_no_existe(tmp_path):
    store = TokenStore(tmp_path / "agent.json")
    store.clear()  # no debe levantar
    assert store.load() is None


# ------------------------------------------------------------- ensure_agent


def test_reusa_el_token_de_la_temporada_actual(settings):
    guardar_credenciales(settings, reset_date=TEMPORADA_ACTUAL)
    sesion, http = sesion_de_prueba(
        settings, [status(), RespuestaFalsa(200, {"data": AGENTE})]
    )

    agente = sesion.ensure_agent()

    assert agente.symbol == "TEST_AGENT"
    assert [ll["url"].split("/v2")[1] for ll in http.llamadas] == ["/", "/my/agent"]
    assert sesion.client.token == "token-guardado"


def test_registra_de_nuevo_cuando_cambio_la_temporada(settings):
    """El caso del sabado: el token guardado es de la semana pasada."""
    guardar_credenciales(settings, reset_date=TEMPORADA_VIEJA)
    sesion, http = sesion_de_prueba(settings, [status(), registro_ok()])

    agente = sesion.ensure_agent()

    assert agente.symbol == "TEST_AGENT"
    rutas = [ll["url"].split("/v2")[1] for ll in http.llamadas]
    assert rutas == ["/", "/register"]
    # El registro se firma con el token de cuenta, no con el viejo del agente.
    assert http.llamadas[1]["headers"]["Authorization"] == "Bearer cuenta-de-prueba"
    # Y las credenciales nuevas quedan atadas a la temporada nueva.
    guardadas = TokenStore(settings.token_file).load()
    assert guardadas.token == "token-nuevo"
    assert guardadas.reset_date == TEMPORADA_ACTUAL


def test_sin_auto_reregister_avisa_del_reset(settings):
    settings.auto_reregister = False
    guardar_credenciales(settings, reset_date=TEMPORADA_VIEJA)
    sesion, _ = sesion_de_prueba(settings, [status()])

    with pytest.raises(ServerResetError) as exc:
        sesion.ensure_agent()

    assert exc.value.stored_reset == TEMPORADA_VIEJA
    assert exc.value.current_reset == TEMPORADA_ACTUAL


def test_un_token_rechazado_se_descarta_y_se_registra(settings):
    """Mismo `resetDate` pero la API dice 401: el token guardado ya no sirve."""
    guardar_credenciales(settings, reset_date=TEMPORADA_ACTUAL)
    sesion, http = sesion_de_prueba(
        settings,
        [
            status(),
            RespuestaFalsa(401, {"error": {"code": 4100, "message": "token invalido"}}),
            registro_ok(),
        ],
    )

    agente = sesion.ensure_agent()

    assert agente.symbol == "TEST_AGENT"
    assert [ll["url"].split("/v2")[1] for ll in http.llamadas] == [
        "/",
        "/my/agent",
        "/register",
    ]


def test_si_cambia_el_simbolo_pedido_se_registra_el_nuevo(settings):
    guardar_credenciales(settings, reset_date=TEMPORADA_ACTUAL, symbol="OTRO_AGENTE")
    sesion, http = sesion_de_prueba(settings, [status(), registro_ok()])

    sesion.ensure_agent()

    assert [ll["url"].split("/v2")[1] for ll in http.llamadas] == ["/", "/register"]
    assert http.llamadas[1]["json"] == {"symbol": "TEST_AGENT", "faction": "COSMIC"}


def test_usa_el_agent_token_del_entorno_sin_registrar(settings):
    settings.agent_token = "token-a-mano"
    sesion, http = sesion_de_prueba(
        settings, [status(), RespuestaFalsa(200, {"data": AGENTE})]
    )

    sesion.ensure_agent()

    assert sesion.client.token == "token-a-mano"
    assert [ll["url"].split("/v2")[1] for ll in http.llamadas] == ["/", "/my/agent"]


def test_un_agent_token_vencido_explica_que_hacer(settings):
    settings.agent_token = "token-de-la-semana-pasada"
    sesion, _ = sesion_de_prueba(
        settings,
        [status(), RespuestaFalsa(401, {"error": {"code": 4100, "message": "invalido"}})],
    )

    with pytest.raises(ConfigError, match="dashboard"):
        sesion.ensure_agent()


def test_falta_el_token_de_cuenta(settings):
    settings.account_token = None
    sesion, _ = sesion_de_prueba(settings, [status()])

    with pytest.raises(ConfigError, match="SPACETRADERS_ACCOUNT_TOKEN"):
        sesion.ensure_agent()


def test_simbolo_ya_reclamado_sugiere_la_salida(settings):
    """La API no deja recuperar el token de un agente existente: hay que avisarlo."""
    sesion, _ = sesion_de_prueba(
        settings,
        [
            status(),
            RespuestaFalsa(
                409,
                {"error": {"code": 4111, "message": "Agent symbol has already been claimed."}},
            ),
        ],
    )

    with pytest.raises(ConfigError) as exc:
        sesion.ensure_agent()

    mensaje = str(exc.value)
    assert "SPACETRADERS_AGENT_TOKEN" in mensaje
    assert "SPACETRADERS_AGENT_SYMBOL" in mensaje


# ---------------------------------------------------------------------- registro


def test_el_registro_normaliza_simbolo_y_faccion(settings):
    sesion, http = sesion_de_prueba(settings, [status(), registro_ok()])

    sesion.register(symbol="mi_bot", faction="cosmic")

    assert http.llamadas[1]["json"] == {"symbol": "MI_BOT", "faction": "COSMIC"}


def test_el_registro_devuelve_agente_contrato_y_token(settings):
    sesion, _ = sesion_de_prueba(settings, [status(), registro_ok("tok-42")])

    registro = sesion.register()

    assert registro.token == "tok-42"
    assert registro.agent.credits == 175000
    assert registro.contract.terms.deliver[0].trade_symbol == "IRON_ORE"
    assert registro.ships == []
