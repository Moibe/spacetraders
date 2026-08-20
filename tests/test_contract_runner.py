"""Tests del bot de contratos: combustible y movimiento. Sin red.

El bot se prueba contra dobles de la capa de flota en vez de modelos completos:
lo que importa aca es el ORDEN de las acciones (recargar antes de salir, caer a
DRIFT si no alcanza), no la deserializacion, que ya cubre test_client.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from bots.contract_runner import ContractRunner
from spacetraders.errors import ApiError


def nave_falsa(
    *,
    fuel: int = 400,
    capacidad: int = 400,
    waypoint: str = "X1-SC86-K91",
    estado: str = "DOCKED",
) -> SimpleNamespace:
    return SimpleNamespace(
        symbol="MOIBE-1",
        fuel=SimpleNamespace(current=fuel, capacity=capacidad),
        nav=SimpleNamespace(
            waypoint_symbol=waypoint, status=estado, system_symbol="X1-SC86"
        ),
        cargo=SimpleNamespace(capacity=40, units=0, inventory=[]),
        registration=SimpleNamespace(role="COMMAND"),
    )


class FlotaFalsa:
    """Doble de `FleetApi` que registra las acciones en orden."""

    def __init__(
        self, nave: SimpleNamespace, *, navigate_error: ApiError | None = None
    ) -> None:
        self.nave = nave
        self.acciones: list[str] = []
        self._navigate_error = navigate_error
        self.sin_combustible_para_drift = False

    # --- lecturas
    def get_ship(self, _symbol: str) -> SimpleNamespace:
        return self.nave

    def get_nav(self, _symbol: str) -> SimpleNamespace:
        return self.nave.nav

    def wait_for_arrival(self, _symbol: str) -> SimpleNamespace:
        return self.nave.nav

    # --- acciones
    def dock(self, _symbol: str) -> SimpleNamespace:
        self.acciones.append("dock")
        self.nave.nav.status = "DOCKED"
        return self.nave.nav

    def orbit(self, _symbol: str) -> SimpleNamespace:
        self.acciones.append("orbit")
        self.nave.nav.status = "IN_ORBIT"
        return self.nave.nav

    def refuel(self, _symbol: str, **_kwargs) -> SimpleNamespace:
        self.acciones.append("refuel")
        self.nave.fuel.current = self.nave.fuel.capacity
        return SimpleNamespace(
            fuel=self.nave.fuel,
            transaction=SimpleNamespace(total_price=292),
            agent=SimpleNamespace(credits=100_000),
        )

    def set_flight_mode(self, _symbol: str, modo) -> SimpleNamespace:
        self.acciones.append(f"flight_mode:{modo}")
        return SimpleNamespace(nav=self.nave.nav, fuel=self.nave.fuel, events=[])

    def navigate(self, _symbol: str, destino: str) -> SimpleNamespace:
        self.acciones.append(f"navigate:{destino}")
        if self._navigate_error is not None and "flight_mode:DRIFT" not in self.acciones:
            raise self._navigate_error
        if self.sin_combustible_para_drift:
            raise self._navigate_error
        self.nave.nav.waypoint_symbol = destino
        return SimpleNamespace(
            nav=SimpleNamespace(route=SimpleNamespace(arrival="2026-08-20T07:00:00Z")),
            fuel=self.nave.fuel,
            events=[],
        )


def corredor(flota: FlotaFalsa) -> ContractRunner:
    sesion = SimpleNamespace(fleet=flota, contracts=None, systems=None)
    return ContractRunner(sesion)  # type: ignore[arg-type]


def error_sin_combustible() -> ApiError:
    return ApiError(
        "Navigate request failed. Ship MOIBE-1 requires 236 more fuel for navigation.",
        status=400,
        code=4203,
    )


# ------------------------------------------------------------------- recargar


def test_recarga_antes_de_salir():
    """El bug que dejo la nave varada: se recargaba recien AL LLEGAR al mercado."""
    flota = FlotaFalsa(nave_falsa(fuel=82))
    corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    # Ya venia atracada de la entrega, asi que no se gasta una peticion en dock.
    assert flota.acciones == ["refuel", "orbit", "navigate:X1-SC86-B7"]
    assert flota.acciones.index("refuel") < flota.acciones.index("navigate:X1-SC86-B7")


def test_no_recarga_si_el_tanque_esta_casi_lleno():
    flota = FlotaFalsa(nave_falsa(fuel=400))
    corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert "refuel" not in flota.acciones


def test_recargar_atraca_si_esta_en_orbita():
    """Recargar exige estar atracado."""
    flota = FlotaFalsa(nave_falsa(fuel=50, estado="IN_ORBIT"))
    corredor(flota).recargar(flota.nave)

    assert flota.acciones == ["dock", "refuel"]


def test_una_sonda_sin_tanque_no_intenta_recargar():
    flota = FlotaFalsa(nave_falsa(fuel=0, capacidad=0))
    corredor(flota).recargar(flota.nave)

    assert flota.acciones == []


def test_si_el_waypoint_no_vende_fuel_sigue_sin_romper():
    """No todos los waypoints tienen mercado; el viaje se intenta igual."""
    flota = FlotaFalsa(nave_falsa(fuel=50))
    flota.refuel = lambda *_a, **_k: (_ for _ in ()).throw(  # type: ignore[assignment]
        ApiError("Market does not sell fuel", status=400, code=4602)
    )

    corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert "navigate:X1-SC86-B7" in flota.acciones


# ---------------------------------------------------------------------- DRIFT


def test_cae_a_drift_cuando_no_alcanza_el_combustible():
    """Con el tanque lleno y aun asi corto, DRIFT gasta 1 y llega igual."""
    flota = FlotaFalsa(nave_falsa(fuel=400), navigate_error=error_sin_combustible())

    corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert flota.acciones == [
        "orbit",
        "navigate:X1-SC86-B7",
        "flight_mode:DRIFT",
        "navigate:X1-SC86-B7",
    ]


def test_si_ni_a_la_deriva_puede_restaura_el_modo_de_vuelo():
    """No hay que dejar la nave configurada en DRIFT para siempre."""
    flota = FlotaFalsa(nave_falsa(fuel=400), navigate_error=error_sin_combustible())
    flota.sin_combustible_para_drift = True

    with pytest.raises(ApiError):
        corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert flota.acciones[-1] == "flight_mode:CRUISE"


def test_otros_errores_de_navegacion_no_se_tapan():
    """Solo el 4203 justifica el DRIFT; el resto tiene que subir."""
    flota = FlotaFalsa(
        nave_falsa(fuel=400),
        navigate_error=ApiError("Ship is in transit", status=400, code=4214),
    )

    with pytest.raises(ApiError):
        corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert not any(a.startswith("flight_mode") for a in flota.acciones)


def test_no_viaja_si_ya_esta_en_el_destino():
    flota = FlotaFalsa(nave_falsa(waypoint="X1-SC86-B7"))
    corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert flota.acciones == []


def test_vuelve_a_orbita_despues_de_atracar_para_recargar():
    """Recargar atraca la nave, y navegar atracado falla con 4236.

    El estado hay que consultarlo a la API: el objeto `nave` que tiene el bot en
    la mano quedo viejo en el momento en que el propio bot la atraco.
    """
    flota = FlotaFalsa(nave_falsa(fuel=82, estado="IN_ORBIT"))
    corredor(flota).viajar(flota.nave, "X1-SC86-B7")

    assert flota.acciones == ["dock", "refuel", "orbit", "navigate:X1-SC86-B7"]
