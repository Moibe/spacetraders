"""Tests del nucleo HTTP: sobre, reintentos, 429 y paginacion. Sin red."""

from __future__ import annotations

from datetime import UTC

import pytest
import requests

from spacetraders.client import ApiClient
from spacetraders.errors import (
    ApiError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TransportError,
    UnauthorizedError,
)
from spacetraders.models import Agent
from spacetraders.ratelimit import RateLimiter

from .conftest import RespuestaFalsa, SesionFalsa

AGENTE = {
    "symbol": "TEST_AGENT",
    "headquarters": "X1-AA11-A1",
    "credits": 175000,
    "startingFaction": "COSMIC",
    "shipCount": 2,
}


def cliente(settings, respuestas, **kwargs) -> tuple[ApiClient, SesionFalsa]:
    sesion = SesionFalsa(respuestas)
    # Limitador sin espera: el ritmo se prueba en test_ratelimit.
    limiter = RateLimiter(rate_per_second=1e6, burst=1000)
    return (
        ApiClient(
            settings, session=sesion, limiter=limiter, sleep=lambda _s: None, **kwargs
        ),
        sesion,
    )


def test_desempaqueta_data(settings):
    c, _ = cliente(settings, [RespuestaFalsa(200, {"data": AGENTE})])
    assert c.get("/my/agent")["symbol"] == "TEST_AGENT"


def test_parsea_al_modelo_pedido(settings):
    c, _ = cliente(settings, [RespuestaFalsa(200, {"data": AGENTE})])
    agente = c.get("/my/agent", model=Agent)
    assert isinstance(agente, Agent)
    # El alias camelCase de la API llega al campo snake_case del modelo.
    assert agente.starting_faction == "COSMIC"
    assert agente.ship_count == 2


def test_manda_el_token_como_bearer(settings):
    c, sesion = cliente(settings, [RespuestaFalsa(200, {"data": AGENTE})], token="abc123")
    c.get("/my/agent")
    assert sesion.llamadas[0]["headers"]["Authorization"] == "Bearer abc123"


def test_token_vacio_pide_peticion_sin_firmar(settings):
    """`token=""` es como se piden los endpoints publicos aunque haya token cargado."""
    c, sesion = cliente(settings, [RespuestaFalsa(200, {"status": "ok"})], token="abc123")
    c.get_status()
    assert "Authorization" not in sesion.llamadas[0]["headers"]


def test_el_token_por_llamada_pisa_al_de_la_sesion(settings):
    """El registro se firma con el token de cuenta, no con el del agente."""
    c, sesion = cliente(settings, [RespuestaFalsa(200, {"data": {}})], token="agente")
    c.post("/register", json={"symbol": "X"}, token="cuenta")
    assert sesion.llamadas[0]["headers"]["Authorization"] == "Bearer cuenta"


@pytest.mark.parametrize(
    ("status", "esperado"),
    [(401, UnauthorizedError), (404, NotFoundError), (422, ApiError)],
)
def test_los_4xx_suben_tipados_y_sin_reintentar(settings, status, esperado):
    payload = {"error": {"code": 4100, "message": "kaput", "requestId": "abc"}}
    c, sesion = cliente(settings, [RespuestaFalsa(status, payload)])

    with pytest.raises(esperado) as exc:
        c.get("/my/agent")

    assert exc.value.code == 4100
    assert exc.value.request_id == "abc"
    assert len(sesion.llamadas) == 1  # no se reintenta un payload invalido


def test_el_429_se_reintenta_respetando_retry_after(settings):
    c, sesion = cliente(
        settings,
        [
            RespuestaFalsa(429, {"error": {"message": "rate"}}, {"Retry-After": "1"}),
            RespuestaFalsa(200, {"data": AGENTE}),
        ],
    )
    assert c.get("/my/agent")["symbol"] == "TEST_AGENT"
    assert len(sesion.llamadas) == 2


def test_el_429_persistente_termina_en_error(settings):
    respuestas = [
        RespuestaFalsa(429, {"error": {"message": "rate"}}, {"Retry-After": "0"})
        for _ in range(settings.max_retries + 1)
    ]
    c, sesion = cliente(settings, respuestas)

    with pytest.raises(RateLimitError):
        c.get("/my/agent")
    assert len(sesion.llamadas) == settings.max_retries + 1


def test_el_429_penaliza_al_limitador_con_el_retry_after(settings):
    """Tras un 429 no alcanza con esperar: hay que dejar el pozo seco."""

    class LimitadorEspia(RateLimiter):
        def __init__(self) -> None:
            super().__init__(rate_per_second=1e6, burst=1000)
            self.penalizaciones: list[float] = []

        def penalize(self, seconds: float) -> None:
            self.penalizaciones.append(seconds)
            super().penalize(seconds)

    limiter = LimitadorEspia()
    sesion = SesionFalsa(
        [
            RespuestaFalsa(429, {"error": {"message": "rate"}}, {"Retry-After": "2"}),
            RespuestaFalsa(200, {"data": AGENTE}),
        ]
    )
    c = ApiClient(settings, session=sesion, limiter=limiter, sleep=lambda _s: None)
    c.get("/my/agent")

    assert limiter.penalizaciones == [2.0]


def test_sin_retry_after_el_429_usa_la_cabecera_de_reset(settings):
    """Si falta `Retry-After`, la espera sale de `X-RateLimit-Reset`."""
    from datetime import datetime, timedelta

    reset = (datetime.now(UTC) + timedelta(seconds=3)).isoformat().replace(
        "+00:00", "Z"
    )
    c, _ = cliente(
        settings,
        [
            RespuestaFalsa(429, {"error": {"message": "rate"}}, {"X-RateLimit-Reset": reset}),
            RespuestaFalsa(200, {"data": AGENTE}),
        ],
    )
    assert c.get("/my/agent")["symbol"] == "TEST_AGENT"


def test_los_5xx_se_reintentan(settings):
    c, sesion = cliente(
        settings,
        [
            RespuestaFalsa(500, {"error": {"message": "boom"}}),
            RespuestaFalsa(200, {"data": AGENTE}),
        ],
    )
    assert c.get("/my/agent")["symbol"] == "TEST_AGENT"
    assert len(sesion.llamadas) == 2


def test_los_5xx_persistentes_terminan_en_error(settings):
    respuestas = [
        RespuestaFalsa(503, {"error": {"message": "boom"}})
        for _ in range(settings.max_retries + 1)
    ]
    c, _ = cliente(settings, respuestas)
    with pytest.raises(ServerError):
        c.get("/my/agent")


def test_los_get_se_reintentan_ante_fallo_de_red(settings):
    c, sesion = cliente(
        settings,
        [
            requests.exceptions.ConnectionError("cable desconectado"),
            RespuestaFalsa(200, {"data": AGENTE}),
        ],
    )
    assert c.get("/my/agent")["symbol"] == "TEST_AGENT"
    assert len(sesion.llamadas) == 2


def test_los_post_no_se_reintentan_ante_fallo_de_red(settings):
    """Reintentar un POST a ciegas podria comprar o entregar dos veces."""
    c, sesion = cliente(
        settings,
        [
            requests.exceptions.ConnectionError("cable desconectado"),
            RespuestaFalsa(200, {"data": AGENTE}),
        ],
    )
    with pytest.raises(TransportError):
        c.post("/my/ships/X/purchase", json={"symbol": "FUEL", "units": 1})
    assert len(sesion.llamadas) == 1


def test_una_respuesta_no_json_no_rompe_el_parseo(settings):
    """Un 502 con HTML del proxy tiene que llegar como ApiError, no como ValueError."""
    respuesta = RespuestaFalsa(400)
    respuesta.content = b"<html>Bad Gateway</html>"
    respuesta.text = "<html>Bad Gateway</html>"
    c, _ = cliente(settings, [respuesta])

    with pytest.raises(ApiError) as exc:
        c.get("/my/agent")
    assert "Bad Gateway" in str(exc.value)


# ------------------------------------------------------------------- paginacion


def pagina(items, total, page, limit=2):
    return RespuestaFalsa(
        200, {"data": items, "meta": {"total": total, "page": page, "limit": limit}}
    )


def test_paginate_recorre_hasta_el_total(settings):
    c, sesion = cliente(
        settings,
        [pagina([{"n": 1}, {"n": 2}], 3, 1), pagina([{"n": 3}], 3, 2)],
    )
    assert [i["n"] for i in c.paginate("/systems", limit=2)] == [1, 2, 3]
    assert [ll["params"]["page"] for ll in sesion.llamadas] == [1, 2]


def test_paginate_corta_con_pagina_vacia(settings):
    """Sin `meta.total` fiable, una pagina vacia es la senal de fin."""
    c, _ = cliente(settings, [pagina([{"n": 1}], 99, 1), pagina([], 99, 2)])
    assert len(list(c.paginate("/systems", limit=1))) == 1


def test_paginate_respeta_max_pages(settings):
    c, sesion = cliente(
        settings,
        [pagina([{"n": 1}, {"n": 2}], 1000, 1), pagina([{"n": 3}, {"n": 4}], 1000, 2)],
    )
    assert len(list(c.paginate("/systems", limit=2, max_pages=2))) == 4
    assert len(sesion.llamadas) == 2


def test_paginate_valida_el_limite(settings):
    c, _ = cliente(settings, [])
    with pytest.raises(ValueError):
        list(c.paginate("/systems", limit=50))


def test_paginate_parsea_modelos_y_conserva_filtros(settings):
    c, sesion = cliente(settings, [pagina([AGENTE], 1, 1)])
    agentes = list(c.paginate("/agents", model=Agent, params={"traits": "MARKETPLACE"}))

    assert isinstance(agentes[0], Agent)
    assert sesion.llamadas[0]["params"]["traits"] == "MARKETPLACE"
