"""Cliente Python para la API de SpaceTraders (v2.3.0).

Arranque rapido:

    from spacetraders import Session

    with Session.from_env() as sesion:
        agente = sesion.ensure_agent()      # registra o reusa el token guardado
        print(agente.symbol, agente.credits)
        for nave in sesion.fleet.list_ships():
            print(nave.symbol, nave.nav.status, nave.nav.waypoint_symbol)
"""

from .client import ApiClient
from .config import Settings
from .errors import (
    ApiError,
    ConfigError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ServerResetError,
    SpaceTradersError,
    TransportError,
    UnauthorizedError,
)
from .ratelimit import RateLimiter
from .session import AgentCredentials, Registration, Session, TokenStore

__version__ = "0.2.0"

__all__ = [
    "AgentCredentials",
    "ApiClient",
    "ApiError",
    "ConfigError",
    "NotFoundError",
    "RateLimitError",
    "RateLimiter",
    "Registration",
    "ServerError",
    "ServerResetError",
    "Session",
    "Settings",
    "SpaceTradersError",
    "TokenStore",
    "TransportError",
    "UnauthorizedError",
    "__version__",
]
