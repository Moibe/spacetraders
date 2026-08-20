"""Agentes: el propio y el resto de los jugadores."""

from __future__ import annotations

from collections.abc import Iterator

from ..models import Agent
from .base import ApiSection


class AgentsApi(ApiSection):
    """Endpoints `/my/agent` y `/agents`.

    El listado publico sirve para ver contra quien se juega; el leaderboard de
    creditos tambien viene en `GET /` (status del servidor).
    """

    def get_my_agent(self) -> Agent:
        return self.client.get("/my/agent", model=Agent)

    def iter_agents(self, *, limit: int = 20, max_pages: int | None = None) -> Iterator[Agent]:
        return self.client.paginate("/agents", model=Agent, limit=limit, max_pages=max_pages)

    def get_agent(self, agent_symbol: str) -> Agent:
        return self.client.get(f"/agents/{agent_symbol}", model=Agent)
