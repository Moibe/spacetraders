"""Sesion de juego: identidad del agente, persistencia del token y resets del servidor.

SpaceTraders resetea el universo todos los sabados. Cada reset borra el progreso e
invalida todos los tokens de agente, asi que un token no vale nada por si solo: vale
junto al `resetDate` en el que se emitio. `Session` guarda ese par, lo compara contra
el status del servidor al arrancar y re-registra el agente cuando detecta temporada
nueva.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .api import ContractsApi, FactionsApi, FleetApi, SystemsApi
from .client import ApiClient
from .config import Settings
from .errors import ApiError, ConfigError, ServerResetError, UnauthorizedError
from .models import Agent, Contract, Ship

log = logging.getLogger("spacetraders.session")

# Codigo de la API cuando el simbolo del agente ya fue reclamado en esta temporada.
CODE_SYMBOL_RECLAMADO = 4111


@dataclass(slots=True)
class AgentCredentials:
    """Token de agente atado a la temporada en la que se emitio."""

    agent_symbol: str
    faction: str
    token: str
    reset_date: str
    created_at: str

    def is_current(self, reset_date: str) -> bool:
        return self.reset_date == reset_date


class TokenStore:
    """Guarda las credenciales del agente en un JSON local.

    El archivo por defecto (`.spacetraders/agent.json`) esta en `.gitignore`:
    contiene un secreto y no debe viajar al repo.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> AgentCredentials | None:
        if not self.path.exists():
            return None
        try:
            datos = json.loads(self.path.read_text(encoding="utf-8"))
            return AgentCredentials(**datos)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            log.warning("no se pudo leer %s (%s); se ignora", self.path, exc)
            return None

    def save(self, credenciales: AgentCredentials) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(credenciales), indent=2) + "\n", encoding="utf-8"
        )
        log.info("credenciales guardadas en %s", self.path)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)


@dataclass(slots=True)
class Registration:
    """Lo que entrega `POST /register`: agente, contrato inicial y naves."""

    agent: Agent
    contract: Contract
    ships: list[Ship]
    token: str


class Session:
    """Punto de entrada del cliente: resuelve la identidad y expone la API por areas.

    Uso tipico:

        sesion = Session.from_env()
        agente = sesion.ensure_agent()
        for nave in sesion.fleet.list_ships():
            print(nave.symbol, nave.nav.status)
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: ApiClient | None = None,
        store: TokenStore | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.client = client or ApiClient(self.settings)
        self.store = store or TokenStore(self.settings.token_file)

        self.contracts = ContractsApi(self.client)
        self.fleet = FleetApi(self.client)
        self.systems = SystemsApi(self.client)
        self.factions = FactionsApi(self.client)

        self._agent: Agent | None = None
        self._reset_date: str | None = None

    @classmethod
    def from_env(cls, **kwargs: Any) -> Session:
        """Construye la sesion leyendo `.env` + variables de entorno."""
        return cls(Settings.from_env(), **kwargs)

    # ------------------------------------------------------------------ status

    def server_status(self) -> dict[str, Any]:
        """Estado del servidor, cacheado en la sesion para no repetir la peticion."""
        estado = self.client.get_status()
        self._reset_date = estado.get("resetDate")
        return estado

    @property
    def reset_date(self) -> str:
        """`resetDate` de la temporada en curso."""
        if self._reset_date is None:
            self.server_status()
        assert self._reset_date is not None
        return self._reset_date

    # ---------------------------------------------------------------- identidad

    @property
    def agent(self) -> Agent:
        """El agente activo; lo resuelve si todavia no se hizo."""
        if self._agent is None:
            return self.ensure_agent()
        return self._agent

    def get_my_agent(self) -> Agent:
        """`GET /my/agent` -- siempre fresco desde la API."""
        agente = self.client.get("/my/agent", model=Agent)
        self._agent = agente
        return agente

    def ensure_agent(self, *, force_register: bool = False) -> Agent:
        """Deja la sesion lista para jugar y devuelve el agente.

        El orden de resolucion es:

        1. `SPACETRADERS_AGENT_TOKEN` si esta puesto (salida de emergencia manual).
        2. El token guardado, si su `resetDate` coincide con la temporada actual.
        3. Registro nuevo con el token de cuenta.

        Si la temporada cambio y `auto_reregister` esta apagado, levanta
        `ServerResetError` en vez de registrar por su cuenta.
        """
        reset_actual = self.reset_date

        if force_register:
            return self.register().agent

        if self.settings.agent_token:
            log.info("usando SPACETRADERS_AGENT_TOKEN del entorno")
            self.client.set_token(self.settings.agent_token)
            agente = self._validar_token()
            if agente is not None:
                return agente
            raise ConfigError(
                "SPACETRADERS_AGENT_TOKEN fue rechazado por la API. "
                "Probablemente sea de una temporada anterior (la actual empezo el "
                f"{reset_actual}); saca uno nuevo del dashboard, o borra la variable "
                "para registrar de cero."
            )

        credenciales = self.store.load()

        if credenciales is not None and not credenciales.is_current(reset_actual):
            log.warning(
                "el token guardado es de la temporada %s y la actual es %s",
                credenciales.reset_date,
                reset_actual,
            )
            if not self.settings.auto_reregister:
                raise ServerResetError(credenciales.reset_date, reset_actual)
            credenciales = None

        simbolo_pedido = self.settings.agent_symbol
        if (
            credenciales is not None
            and simbolo_pedido is not None
            and credenciales.agent_symbol != simbolo_pedido
        ):
            log.warning(
                "el token guardado es de %s pero se pidio %s; se registra el nuevo",
                credenciales.agent_symbol,
                simbolo_pedido,
            )
            credenciales = None

        if credenciales is not None:
            self.client.set_token(credenciales.token)
            agente = self._validar_token()
            if agente is not None:
                return agente
            log.warning("el token guardado ya no sirve; se descarta")
            self.store.clear()

        if not self.settings.auto_reregister:
            raise ConfigError(
                "No hay token de agente valido y auto_reregister esta apagado. "
                "Corre `python -m spacetraders register` a mano."
            )

        return self.register().agent

    def _validar_token(self) -> Agent | None:
        """Confirma contra `GET /my/agent` que el token sirve. `None` si fue rechazado."""
        try:
            return self.get_my_agent()
        except UnauthorizedError:
            return None

    # ----------------------------------------------------------------- registro

    def register(
        self,
        symbol: str | None = None,
        faction: str | None = None,
    ) -> Registration:
        """`POST /register` -- crea el agente y guarda su token.

        Es el unico endpoint que se firma con el token de *cuenta*. Regala nave de
        comando, sonda, contrato inicial y 175.000 creditos.
        """
        simbolo = (symbol or self.settings.require_agent_symbol()).upper()
        faccion = (faction or self.settings.faction).upper()
        account_token = self.settings.require_account_token()
        # La temporada se consulta ANTES de registrar: si se leyera despues y el
        # servidor se reseteara justo en el medio, se guardaria el token nuevo con
        # el `resetDate` equivocado y el arranque siguiente lo creeria vigente.
        temporada = self.reset_date

        log.info("registrando agente %s en la faccion %s", simbolo, faccion)
        try:
            data = self.client.post(
                "/register",
                json={"symbol": simbolo, "faction": faccion},
                token=account_token,
            )
        except ApiError as exc:
            if exc.code == CODE_SYMBOL_RECLAMADO:
                raise ConfigError(
                    f"El simbolo {simbolo!r} ya esta reclamado en esta temporada y "
                    "la API no permite recuperar su token. Opciones: usar otro "
                    "SPACETRADERS_AGENT_SYMBOL, o copiar el token del agente desde el "
                    "dashboard a SPACETRADERS_AGENT_TOKEN."
                ) from exc
            raise

        token = data["token"]
        credenciales = AgentCredentials(
            agent_symbol=simbolo,
            faction=faccion,
            token=token,
            reset_date=temporada,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self.store.save(credenciales)
        self.client.set_token(token)

        registro = Registration(
            agent=Agent.model_validate(data["agent"]),
            contract=Contract.model_validate(data["contract"]),
            ships=[Ship.model_validate(s) for s in data.get("ships", [])],
            token=token,
        )
        self._agent = registro.agent
        log.info(
            "agente %s listo: %s creditos, %s naves",
            registro.agent.symbol,
            registro.agent.credits,
            len(registro.ships),
        )
        return registro

    # ------------------------------------------------------------------ cierre

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> Session:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
