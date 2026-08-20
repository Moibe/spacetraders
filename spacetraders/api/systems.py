"""Universo: sistemas, waypoints, mercados, astilleros y construcciones."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import (
    Construction,
    JumpGate,
    Market,
    Shipyard,
    System,
    Waypoint,
    WaypointTraitSymbol,
    WaypointType,
)
from .base import ApiSection
from .results import ConstructionSupply


def system_of(waypoint_symbol: str) -> str:
    """Extrae el simbolo del sistema de un simbolo de waypoint.

    Los simbolos tienen forma `SECTOR-SISTEMA-WAYPOINT` (ej. `X1-DF55-20250Z`),
    asi que el sistema son los dos primeros segmentos. Sirve para no tener que
    pasear el simbolo del sistema por todas las funciones.
    """
    partes = waypoint_symbol.split("-")
    if len(partes) < 2:
        raise ValueError(f"{waypoint_symbol!r} no parece un simbolo de waypoint")
    return "-".join(partes[:2])


class SystemsApi(ApiSection):
    """Endpoints publicos `/systems` y `/market`.

    Todo esto se puede consultar con cualquier token de agente: es el mapa del
    juego, no depende de tu flota.
    """

    # ---------------------------------------------------------------- sistemas

    def iter_systems(
        self, *, limit: int = 20, max_pages: int | None = None
    ) -> Iterator[System]:
        """Recorre todos los sistemas del universo (son miles: usa `max_pages`)."""
        return self.client.paginate(
            "/systems", model=System, limit=limit, max_pages=max_pages
        )

    def get_system(self, system_symbol: str) -> System:
        return self.client.get(f"/systems/{system_symbol}", model=System)

    # ---------------------------------------------------------------- waypoints

    def iter_waypoints(
        self,
        system_symbol: str,
        *,
        traits: str | WaypointTraitSymbol | list[str] | None = None,
        waypoint_type: str | WaypointType | None = None,
        limit: int = 20,
        max_pages: int | None = None,
    ) -> Iterator[Waypoint]:
        """Recorre los waypoints de un sistema, con filtros del lado del servidor.

        Filtrar en la API en vez de en Python ahorra peticiones, y las
        peticiones son el recurso escaso (2 por segundo).
        """
        params: dict[str, Any] = {}
        if traits is not None:
            params["traits"] = (
                [str(t) for t in traits] if isinstance(traits, list) else str(traits)
            )
        if waypoint_type is not None:
            params["type"] = str(waypoint_type)
        return self.client.paginate(
            f"/systems/{system_symbol}/waypoints",
            model=Waypoint,
            params=params or None,
            limit=limit,
            max_pages=max_pages,
        )

    def list_waypoints(self, system_symbol: str, **kwargs: Any) -> list[Waypoint]:
        return list(self.iter_waypoints(system_symbol, **kwargs))

    def get_waypoint(self, waypoint_symbol: str) -> Waypoint:
        sistema = system_of(waypoint_symbol)
        return self.client.get(
            f"/systems/{sistema}/waypoints/{waypoint_symbol}", model=Waypoint
        )

    def find_marketplaces(self, system_symbol: str) -> list[Waypoint]:
        """Waypoints con mercado en el sistema."""
        return self.list_waypoints(system_symbol, traits=WaypointTraitSymbol.marketplace)

    def find_shipyards(self, system_symbol: str) -> list[Waypoint]:
        """Waypoints con astillero en el sistema."""
        return self.list_waypoints(system_symbol, traits=WaypointTraitSymbol.shipyard)

    # ------------------------------------------------------------------ mercados

    def get_market(self, waypoint_symbol: str) -> Market:
        """Mercado de un waypoint.

        Los precios (`trade_goods`) solo vienen si tenes una nave presente en ese
        waypoint; si no, solo se ven las listas de imports/exports/exchange.
        """
        sistema = system_of(waypoint_symbol)
        return self.client.get(
            f"/systems/{sistema}/waypoints/{waypoint_symbol}/market", model=Market
        )

    def get_shipyard(self, waypoint_symbol: str) -> Shipyard:
        """Astillero de un waypoint (precios visibles solo con nave presente)."""
        sistema = system_of(waypoint_symbol)
        return self.client.get(
            f"/systems/{sistema}/waypoints/{waypoint_symbol}/shipyard", model=Shipyard
        )

    def get_supply_chain(self) -> dict[str, Any]:
        """Mapa global de que exportacion alimenta a que importacion."""
        data = self.client.get("/market/supply-chain")
        return data or {}

    # -------------------------------------------------------- jump gates y obras

    def get_jump_gate(self, waypoint_symbol: str) -> JumpGate:
        sistema = system_of(waypoint_symbol)
        return self.client.get(
            f"/systems/{sistema}/waypoints/{waypoint_symbol}/jump-gate", model=JumpGate
        )

    def get_construction(self, waypoint_symbol: str) -> Construction:
        sistema = system_of(waypoint_symbol)
        return self.client.get(
            f"/systems/{sistema}/waypoints/{waypoint_symbol}/construction",
            model=Construction,
        )

    def supply_construction(
        self, waypoint_symbol: str, ship_symbol: str, trade_symbol: str, units: int
    ) -> ConstructionSupply:
        """Aporta materiales a una obra (por ejemplo, reparar un jump gate)."""
        sistema = system_of(waypoint_symbol)
        data = self.client.post(
            f"/systems/{sistema}/waypoints/{waypoint_symbol}/construction/supply",
            json={
                "shipSymbol": ship_symbol,
                "tradeSymbol": str(trade_symbol),
                "units": units,
            },
        )
        return ConstructionSupply.model_validate(data)
