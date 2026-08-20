"""Tests del token bucket, con reloj falso: no esperan de verdad."""

from __future__ import annotations

import pytest

from spacetraders.ratelimit import RateLimiter


class RelojFalso:
    """Reloj monotono controlado a mano; el sleep adelanta el tiempo."""

    def __init__(self) -> None:
        self.ahora = 0.0
        self.dormidas: list[float] = []

    def clock(self) -> float:
        return self.ahora

    def sleep(self, segundos: float) -> None:
        self.dormidas.append(segundos)
        self.ahora += segundos


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


def limitador(reloj: RelojFalso, **kwargs) -> RateLimiter:
    return RateLimiter(clock=reloj.clock, sleep=reloj.sleep, **kwargs)


def test_la_rafaga_no_espera(reloj):
    rl = limitador(reloj, rate_per_second=2, burst=30)
    esperas = [rl.acquire() for _ in range(30)]
    assert esperas == [0.0] * 30
    assert reloj.dormidas == []


def test_pasada_la_rafaga_se_espera_el_ritmo_sostenido(reloj):
    rl = limitador(reloj, rate_per_second=2, burst=30)
    for _ in range(30):
        rl.acquire()

    # A 2 tokens por segundo, el siguiente tarda medio segundo.
    assert rl.acquire() == pytest.approx(0.5)
    assert rl.acquire() == pytest.approx(0.5)


def test_el_pozo_se_recarga_con_el_tiempo(reloj):
    rl = limitador(reloj, rate_per_second=2, burst=10)
    for _ in range(10):
        rl.acquire()
    assert rl.available == pytest.approx(0.0)

    reloj.ahora += 3.0  # 3 s * 2/s = 6 tokens
    assert rl.available == pytest.approx(6.0)


def test_la_recarga_no_pasa_de_la_capacidad(reloj):
    rl = limitador(reloj, rate_per_second=2, burst=5)
    reloj.ahora += 1000
    assert rl.available == pytest.approx(5.0)


def test_penalize_seca_el_pozo_y_atrasa_la_recarga(reloj):
    rl = limitador(reloj, rate_per_second=2, burst=30)
    rl.penalize(2.0)

    assert rl.available == pytest.approx(0.0)
    # Aun pasado 1 s sigue seco, porque la penalizacion corre 2 s.
    reloj.ahora += 1.0
    assert rl.available == pytest.approx(0.0)
    # Pasada la penalizacion, la recarga arranca de nuevo.
    reloj.ahora += 2.0
    assert rl.available == pytest.approx(2.0)


@pytest.mark.parametrize(
    "kwargs",
    [{"rate_per_second": 0}, {"rate_per_second": -1}, {"burst": 0}],
)
def test_configuracion_invalida(reloj, kwargs):
    with pytest.raises(ValueError):
        limitador(reloj, **kwargs)
