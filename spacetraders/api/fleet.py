"""Flota: naves, navegacion, carga, mineria, mercado a bordo y modificaciones."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any

from ..errors import SpaceTradersError
from ..models import (
    Cooldown,
    Ship,
    ShipCargo,
    ShipModule,
    ShipMount,
    ShipNav,
    ShipNavFlightMode,
    ShipType,
    Survey,
)
from .base import ApiSection, payload
from .results import (
    ChartResult,
    ExtractionResult,
    JumpResult,
    MarketOperation,
    ModuleChange,
    MountChange,
    NavigationResult,
    RefineResult,
    RefuelResult,
    RepairResult,
    ScrapResult,
    ShipPurchase,
    ShipScan,
    SiphonResult,
    SurveyResult,
    SystemScan,
    WaypointScan,
)

log = logging.getLogger("spacetraders.fleet")


class FleetApi(ApiSection):
    """Endpoints `/my/ships`. Es el corazon del juego: todo lo que hace una nave."""

    # -------------------------------------------------------------- inventario

    def iter_ships(self, *, limit: int = 20) -> Iterator[Ship]:
        """Recorre la flota pagina por pagina."""
        return self.client.paginate("/my/ships", model=Ship, limit=limit)

    def list_ships(self, *, limit: int = 20) -> list[Ship]:
        """Toda la flota de una vez."""
        return list(self.iter_ships(limit=limit))

    def get_ship(self, ship_symbol: str) -> Ship:
        return self.client.get(f"/my/ships/{ship_symbol}", model=Ship)

    def get_cargo(self, ship_symbol: str) -> ShipCargo:
        return self.client.get(f"/my/ships/{ship_symbol}/cargo", model=ShipCargo)

    def get_nav(self, ship_symbol: str) -> ShipNav:
        return self.client.get(f"/my/ships/{ship_symbol}/nav", model=ShipNav)

    def get_cooldown(self, ship_symbol: str) -> Cooldown | None:
        """Cooldown activo de la nave, o `None` si esta lista para actuar.

        La API responde 204 sin cuerpo cuando no hay cooldown.
        """
        data = self.client.get(f"/my/ships/{ship_symbol}/cooldown")
        return Cooldown.model_validate(data) if data else None

    def purchase_ship(self, ship_type: ShipType | str, waypoint_symbol: str) -> ShipPurchase:
        """Compra una nave en el astillero del waypoint indicado."""
        data = self.client.post(
            "/my/ships",
            json={"shipType": str(ship_type), "waypointSymbol": waypoint_symbol},
        )
        return ShipPurchase.model_validate(data)

    # -------------------------------------------------------------- navegacion

    def orbit(self, ship_symbol: str) -> ShipNav:
        """Pone la nave en orbita (requisito para navegar o minar)."""
        data = self.client.post(f"/my/ships/{ship_symbol}/orbit")
        return ShipNav.model_validate(data["nav"])

    def dock(self, ship_symbol: str) -> ShipNav:
        """Atraca la nave (requisito para comerciar, recargar o entregar)."""
        data = self.client.post(f"/my/ships/{ship_symbol}/dock")
        return ShipNav.model_validate(data["nav"])

    def navigate(self, ship_symbol: str, waypoint_symbol: str) -> NavigationResult:
        """Vuela dentro del sistema. Consume combustible y tarda: el tiempo de
        llegada viene en `nav.route.arrival`."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/navigate",
            json={"waypointSymbol": waypoint_symbol},
        )
        return NavigationResult.model_validate(data)

    def warp(self, ship_symbol: str, waypoint_symbol: str) -> NavigationResult:
        """Viaja a otro sistema sin jump gate (caro en combustible)."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/warp",
            json={"waypointSymbol": waypoint_symbol},
        )
        return NavigationResult.model_validate(data)

    def jump(self, ship_symbol: str, waypoint_symbol: str) -> JumpResult:
        """Salta a otro sistema por jump gate: instantaneo, cuesta creditos y deja cooldown."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/jump",
            json={"waypointSymbol": waypoint_symbol},
        )
        return JumpResult.model_validate(data)

    def wait_for_arrival(
        self,
        ship_symbol: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ) -> ShipNav:
        """Espera a que la nave termine su viaje y devuelve su nav final.

        La estimacion sale de `nav.route.arrival` corregida por el desfase de reloj
        del cliente, pero la verdad la tiene la API: despues de dormir lo estimado
        se vuelve a preguntar, y si sigue en transito se sondea cada
        `poll_interval`. Sin ese sondeo, un reloj local corrido hace que la accion
        siguiente falle con "ship is currently in-transit".
        """
        nav = self.get_nav(ship_symbol)
        inicio = time.monotonic()

        while str(nav.status) == "IN_TRANSIT":
            if time.monotonic() - inicio > timeout:
                raise SpaceTradersError(
                    f"{ship_symbol} sigue en transito despues de {timeout:.0f}s "
                    f"(llegada estimada {nav.route.arrival})"
                )
            restante = (nav.route.arrival - self.client.server_now()).total_seconds() + 1
            espera = restante if restante > 0 else poll_interval
            log.info("%s en transito; esperando %.0fs", ship_symbol, espera)
            time.sleep(espera)
            nav = self.get_nav(ship_symbol)

        return nav

    def set_flight_mode(
        self, ship_symbol: str, flight_mode: ShipNavFlightMode | str
    ) -> NavigationResult:
        """Cambia el modo de vuelo (DRIFT gasta casi nada pero es lentisimo;
        CRUISE es el default; BURN es rapido y caro; STEALTH evita escaneos)."""
        data = self.client.patch(
            f"/my/ships/{ship_symbol}/nav",
            json={"flightMode": str(flight_mode)},
        )
        return NavigationResult.model_validate(data)

    # ------------------------------------------------------------------ carga

    def purchase_cargo(
        self, ship_symbol: str, trade_symbol: str, units: int
    ) -> MarketOperation:
        """Compra mercancia en el mercado del waypoint (hay que estar atracado)."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/purchase",
            json={"symbol": str(trade_symbol), "units": units},
        )
        return MarketOperation.model_validate(data)

    def sell_cargo(self, ship_symbol: str, trade_symbol: str, units: int) -> MarketOperation:
        """Vende mercancia en el mercado del waypoint (hay que estar atracado)."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/sell",
            json={"symbol": str(trade_symbol), "units": units},
        )
        return MarketOperation.model_validate(data)

    def jettison(self, ship_symbol: str, trade_symbol: str, units: int) -> ShipCargo:
        """Tira carga al espacio para hacer lugar."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/jettison",
            json={"symbol": str(trade_symbol), "units": units},
        )
        return ShipCargo.model_validate(data["cargo"])

    def transfer_cargo(
        self, ship_symbol: str, target_ship_symbol: str, trade_symbol: str, units: int
    ) -> ShipCargo:
        """Pasa carga a otra nave propia en el mismo waypoint.

        Devuelve la carga de la nave *origen*.
        """
        data = self.client.post(
            f"/my/ships/{ship_symbol}/transfer",
            json={
                "shipSymbol": target_ship_symbol,
                "tradeSymbol": str(trade_symbol),
                "units": units,
            },
        )
        return ShipCargo.model_validate(data["cargo"])

    def refuel(
        self, ship_symbol: str, *, units: int | None = None, from_cargo: bool = False
    ) -> RefuelResult:
        """Recarga combustible. Sin `units` llena el tanque.

        `from_cargo=True` usa FUEL que la nave ya lleva en la bodega, lo que permite
        recargar donde no hay mercado.
        """
        cuerpo: dict[str, Any] = {"fromCargo": from_cargo}
        if units is not None:
            cuerpo["units"] = units
        data = self.client.post(f"/my/ships/{ship_symbol}/refuel", json=cuerpo)
        return RefuelResult.model_validate(data)

    # --------------------------------------------------------------- extraccion

    def create_survey(self, ship_symbol: str) -> SurveyResult:
        """Mapea los depositos del waypoint para minar con mejor rendimiento."""
        data = self.client.post(f"/my/ships/{ship_symbol}/survey")
        return SurveyResult.model_validate(data)

    def extract(self, ship_symbol: str, survey: Survey | None = None) -> ExtractionResult:
        """Mina el waypoint. Con `survey` el rinde es mejor y apunta a lo que interesa."""
        if survey is None:
            data = self.client.post(f"/my/ships/{ship_symbol}/extract")
        else:
            # El endpoint dedicado recibe el survey como cuerpo completo.
            data = self.client.post(
                f"/my/ships/{ship_symbol}/extract/survey", json=payload(survey)
            )
        return ExtractionResult.model_validate(data)

    def siphon(self, ship_symbol: str) -> SiphonResult:
        """Sifonea gas de un gigante gaseoso (necesita mount de sifon)."""
        data = self.client.post(f"/my/ships/{ship_symbol}/siphon")
        return SiphonResult.model_validate(data)

    def refine(self, ship_symbol: str, produce: str) -> RefineResult:
        """Refina mineral en bruto a bordo (necesita modulo refinador)."""
        data = self.client.post(
            f"/my/ships/{ship_symbol}/refine", json={"produce": str(produce)}
        )
        return RefineResult.model_validate(data)

    # ------------------------------------------------------------------ escaneo

    def scan_systems(self, ship_symbol: str) -> SystemScan:
        data = self.client.post(f"/my/ships/{ship_symbol}/scan/systems")
        return SystemScan.model_validate(data)

    def scan_waypoints(self, ship_symbol: str) -> WaypointScan:
        data = self.client.post(f"/my/ships/{ship_symbol}/scan/waypoints")
        return WaypointScan.model_validate(data)

    def scan_ships(self, ship_symbol: str) -> ShipScan:
        data = self.client.post(f"/my/ships/{ship_symbol}/scan/ships")
        return ShipScan.model_validate(data)

    # ----------------------------------------------------------- modificaciones

    def get_mounts(self, ship_symbol: str) -> list[ShipMount]:
        data = self.client.get(f"/my/ships/{ship_symbol}/mounts")
        return [ShipMount.model_validate(m) for m in data]

    def install_mount(self, ship_symbol: str, mount_symbol: str) -> MountChange:
        data = self.client.post(
            f"/my/ships/{ship_symbol}/mounts/install", json={"symbol": str(mount_symbol)}
        )
        return MountChange.model_validate(data)

    def remove_mount(self, ship_symbol: str, mount_symbol: str) -> MountChange:
        data = self.client.post(
            f"/my/ships/{ship_symbol}/mounts/remove", json={"symbol": str(mount_symbol)}
        )
        return MountChange.model_validate(data)

    def get_modules(self, ship_symbol: str) -> list[ShipModule]:
        data = self.client.get(f"/my/ships/{ship_symbol}/modules")
        return [ShipModule.model_validate(m) for m in data]

    def install_module(self, ship_symbol: str, module_symbol: str) -> ModuleChange:
        data = self.client.post(
            f"/my/ships/{ship_symbol}/modules/install", json={"symbol": str(module_symbol)}
        )
        return ModuleChange.model_validate(data)

    def remove_module(self, ship_symbol: str, module_symbol: str) -> ModuleChange:
        data = self.client.post(
            f"/my/ships/{ship_symbol}/modules/remove", json={"symbol": str(module_symbol)}
        )
        return ModuleChange.model_validate(data)

    # ----------------------------------------------------- reparacion y desguace

    def get_repair_cost(self, ship_symbol: str) -> dict[str, Any]:
        """Cotiza la reparacion sin ejecutarla."""
        return self.client.get(f"/my/ships/{ship_symbol}/repair")

    def repair(self, ship_symbol: str) -> RepairResult:
        """Repara la nave (hay que estar atracado en un astillero)."""
        data = self.client.post(f"/my/ships/{ship_symbol}/repair")
        return RepairResult.model_validate(data)

    def get_scrap_value(self, ship_symbol: str) -> dict[str, Any]:
        """Cotiza el desguace sin ejecutarlo."""
        return self.client.get(f"/my/ships/{ship_symbol}/scrap")

    def scrap(self, ship_symbol: str) -> ScrapResult:
        """Desguaza la nave a cambio de creditos. Es irreversible."""
        data = self.client.post(f"/my/ships/{ship_symbol}/scrap")
        return ScrapResult.model_validate(data)

    # ---------------------------------------------------------------- cartografia

    def chart_waypoint(self, ship_symbol: str) -> ChartResult:
        """Cartografia el waypoint actual si nadie lo mapeo antes."""
        data = self.client.post(f"/my/ships/{ship_symbol}/chart")
        return ChartResult.model_validate(data)
