"""Tests de la capa de flota: espera de llegada y desfase de reloj. Sin red."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from spacetraders.api import FleetApi
from spacetraders.client import ApiClient
from spacetraders.errors import SpaceTradersError
from spacetraders.ratelimit import RateLimiter

from .conftest import RespuestaFalsa, SesionFalsa


def waypoint(simbolo: str = "X1-SC86-A1") -> dict:
    return {
        "symbol": simbolo,
        "type": "PLANET",
        "systemSymbol": "X1-SC86",
        "x": 0,
        "y": 0,
    }


def nav(estado: str, *, llegada: datetime, destino: str = "X1-SC86-B7") -> RespuestaFalsa:
    return RespuestaFalsa(
        200,
        {
            "data": {
                "systemSymbol": "X1-SC86",
                "waypointSymbol": destino,
                "status": estado,
                "flightMode": "CRUISE",
                "route": {
                    "destination": waypoint(destino),
                    "origin": waypoint(),
                    "departureTime": "2026-08-20T06:00:00.000Z",
                    "arrival": llegada.isoformat().replace("+00:00", "Z"),
                },
            }
        },
    )


def flota(respuestas) -> tuple[FleetApi, SesionFalsa, list[float]]:
    """FleetApi con sesion falsa; devuelve tambien las esperas registradas."""
    http = SesionFalsa(respuestas)
    cliente = ApiClient(
        session=http,
        limiter=RateLimiter(rate_per_second=1e6, burst=1000),
        sleep=lambda _s: None,
    )
    return FleetApi(cliente), http, []


def test_no_espera_si_la_nave_ya_llego():
    fleet, http, _ = flota([nav("IN_ORBIT", llegada=datetime.now(UTC))])

    resultado = fleet.wait_for_arrival("MOIBE-1")

    assert str(resultado.status) == "IN_ORBIT"
    assert len(http.llamadas) == 1  # una sola consulta de nav


def test_espera_y_vuelve_a_preguntar_hasta_que_aterriza(monkeypatch):
    """La API es la verdad: tras dormir lo estimado se re-consulta el estado."""
    esperas: list[float] = []
    monkeypatch.setattr("time.sleep", esperas.append)

    fleet, http, _ = flota(
        [
            nav("IN_TRANSIT", llegada=datetime.now(UTC) + timedelta(seconds=30)),
            # La llegada estimada ya paso pero la nave sigue en transito: aca es
            # donde un cliente que confia solo en el reloj falla con "in-transit".
            nav("IN_TRANSIT", llegada=datetime.now(UTC) - timedelta(seconds=1)),
            nav("IN_ORBIT", llegada=datetime.now(UTC) - timedelta(seconds=1)),
        ]
    )

    resultado = fleet.wait_for_arrival("MOIBE-1", poll_interval=5.0)

    assert str(resultado.status) == "IN_ORBIT"
    assert len(http.llamadas) == 3
    # Primera espera: lo estimado (~31s). Segunda: el intervalo de sondeo.
    assert esperas[0] == pytest.approx(31, abs=2)
    assert esperas[1] == pytest.approx(5.0)


def test_corrige_la_espera_con_el_desfase_del_reloj(monkeypatch):
    """Con el reloj local 89s adelantado, la espera debe ser 89s mas larga."""
    esperas: list[float] = []
    monkeypatch.setattr("time.sleep", esperas.append)

    llegada = datetime.now(UTC) + timedelta(seconds=30)
    respuesta_en_transito = nav("IN_TRANSIT", llegada=llegada)
    # `Date` del servidor 89s atras respecto del reloj local.
    hora_servidor = datetime.now(UTC) - timedelta(seconds=89)
    respuesta_en_transito.headers["Date"] = hora_servidor.strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    fleet, _, _ = flota([respuesta_en_transito, nav("IN_ORBIT", llegada=llegada)])
    fleet.wait_for_arrival("MOIBE-1")

    assert fleet.client.clock_skew == pytest.approx(-89, abs=2)
    assert esperas[0] == pytest.approx(120, abs=3)  # 30 + 89 + 1 de colchon


def test_la_espera_no_es_infinita(monkeypatch):
    """Si la nave nunca aterriza, se corta en vez de colgar el bot para siempre."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    reloj = iter([0.0, 0.0, 10_000.0])
    monkeypatch.setattr("time.monotonic", lambda: next(reloj))

    llegada = datetime.now(UTC) - timedelta(seconds=1)
    fleet, _, _ = flota([nav("IN_TRANSIT", llegada=llegada)] * 3)

    with pytest.raises(SpaceTradersError, match="sigue en transito"):
        fleet.wait_for_arrival("MOIBE-1", timeout=60)


def test_un_date_invalido_no_rompe_nada():
    respuesta = nav("IN_ORBIT", llegada=datetime.now(UTC))
    respuesta.headers["Date"] = "no es una fecha"

    fleet, _, _ = flota([respuesta])
    fleet.wait_for_arrival("MOIBE-1")

    assert fleet.client.clock_skew == 0.0
