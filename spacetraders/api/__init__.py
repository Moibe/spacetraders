"""Capa de recursos: un modulo por area del juego.

Cada clase recibe un `ApiClient` y traduce endpoints a metodos con tipos. La
composicion vive en `spacetraders.session.Session`, que las expone como
`sesion.fleet`, `sesion.contracts`, etc.
"""

from .agents import AgentsApi
from .base import ApiSection
from .contracts import ContractsApi
from .factions import FactionsApi
from .fleet import FleetApi
from .systems import SystemsApi, system_of

__all__ = [
    "AgentsApi",
    "ApiSection",
    "ContractsApi",
    "FactionsApi",
    "FleetApi",
    "SystemsApi",
    "system_of",
]
