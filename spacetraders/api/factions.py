"""Facciones del juego."""

from __future__ import annotations

from collections.abc import Iterator

from ..models import Faction
from .base import ApiSection


class FactionsApi(ApiSection):
    """Endpoints `/factions`.

    La faccion elegida al registrarse define el sistema de origen, y su
    `headquarters` es donde arranca tu flota.
    """

    def iter_factions(self, *, limit: int = 20) -> Iterator[Faction]:
        return self.client.paginate("/factions", model=Faction, limit=limit)

    def list_factions(self, *, limit: int = 20) -> list[Faction]:
        return list(self.iter_factions(limit=limit))

    def get_faction(self, faction_symbol: str) -> Faction:
        return self.client.get(f"/factions/{faction_symbol}", model=Faction)

    def recruiting(self) -> list[Faction]:
        """Facciones que aceptan agentes nuevos (las unicas validas al registrarse)."""
        return [f for f in self.iter_factions() if f.is_recruiting]
