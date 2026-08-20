"""Configuracion del cliente, leida de variables de entorno / `.env`."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .errors import ConfigError

BASE_URL = "https://api.spacetraders.io/v2"

# La API valida el simbolo del agente con Zod: string de 3 a 14 caracteres.
SYMBOL_MIN_LEN = 3
SYMBOL_MAX_LEN = 14

DEFAULT_TOKEN_FILE = ".spacetraders/agent.json"
DEFAULT_FACTION = "COSMIC"


@dataclass(slots=True)
class Settings:
    """Todo lo que el cliente necesita saber para arrancar.

    `account_token` sale del dashboard de SpaceTraders y solo sirve para
    `POST /register`. El token de agente (el que firma los otros 54 endpoints)
    lo emite el registro y se guarda en `token_file`.

    `agent_token` es la salida de emergencia: si el simbolo ya esta reclamado en
    esta temporada, la API no permite recuperar su token, asi que se pega a mano
    desde el dashboard y el cliente se saltea el registro.
    """

    account_token: str | None = None
    agent_token: str | None = None
    agent_symbol: str | None = None
    faction: str = DEFAULT_FACTION
    token_file: Path = field(default_factory=lambda: Path(DEFAULT_TOKEN_FILE))
    base_url: str = BASE_URL
    timeout: float = 30.0
    max_retries: int = 5
    auto_reregister: bool = True

    @classmethod
    def from_env(cls, *, dotenv_path: str | os.PathLike[str] | None = None) -> Settings:
        """Carga la configuracion desde `.env` + entorno.

        Las variables de entorno reales ganan sobre el `.env` (util en CI).
        """
        load_dotenv(dotenv_path=dotenv_path, override=False)

        simbolo = _limpiar(os.getenv("SPACETRADERS_AGENT_SYMBOL"))
        if simbolo:
            simbolo = simbolo.upper()

        token_file = _limpiar(os.getenv("SPACETRADERS_TOKEN_FILE")) or DEFAULT_TOKEN_FILE

        settings = cls(
            account_token=_limpiar(os.getenv("SPACETRADERS_ACCOUNT_TOKEN")),
            agent_token=_limpiar(os.getenv("SPACETRADERS_AGENT_TOKEN")),
            agent_symbol=simbolo,
            faction=(_limpiar(os.getenv("SPACETRADERS_FACTION")) or DEFAULT_FACTION).upper(),
            token_file=Path(token_file),
            base_url=_limpiar(os.getenv("SPACETRADERS_BASE_URL")) or BASE_URL,
            timeout=_flotante("SPACETRADERS_TIMEOUT", 30.0),
            max_retries=int(_flotante("SPACETRADERS_MAX_RETRIES", 5)),
            auto_reregister=_booleano("SPACETRADERS_AUTO_REREGISTER", True),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Valida lo que se pueda antes de gastar una peticion contra la API."""
        if self.agent_symbol is not None:
            largo = len(self.agent_symbol)
            if not SYMBOL_MIN_LEN <= largo <= SYMBOL_MAX_LEN:
                raise ConfigError(
                    f"SPACETRADERS_AGENT_SYMBOL={self.agent_symbol!r} tiene {largo} "
                    "caracteres; "
                    f"la API exige entre {SYMBOL_MIN_LEN} y {SYMBOL_MAX_LEN}."
                )
        if self.max_retries < 0:
            raise ConfigError("SPACETRADERS_MAX_RETRIES no puede ser negativo.")
        if self.timeout <= 0:
            raise ConfigError("SPACETRADERS_TIMEOUT debe ser > 0.")

    def require_account_token(self) -> str:
        """Devuelve el token de cuenta o explica como conseguirlo."""
        if not self.account_token:
            raise ConfigError(
                "Falta SPACETRADERS_ACCOUNT_TOKEN. Se saca del dashboard "
                "(https://my.spacetraders.io) y es el unico token que acepta POST /register. "
                "Copialo en tu archivo .env."
            )
        return self.account_token

    def require_agent_symbol(self) -> str:
        """Devuelve el simbolo del agente o explica que falta."""
        if not self.agent_symbol:
            raise ConfigError(
                "Falta SPACETRADERS_AGENT_SYMBOL (3-14 caracteres). "
                "Es el nombre de tu agente y prefija el simbolo de cada nave que compres."
            )
        return self.agent_symbol


def _limpiar(valor: str | None) -> str | None:
    """Normaliza un valor de entorno: recorta espacios y trata el vacio como ausente."""
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


def _flotante(nombre: str, default: float) -> float:
    crudo = _limpiar(os.getenv(nombre))
    if crudo is None:
        return default
    try:
        return float(crudo)
    except ValueError as exc:
        raise ConfigError(f"{nombre}={crudo!r} no es un numero valido.") from exc


def _booleano(nombre: str, default: bool) -> bool:
    crudo = _limpiar(os.getenv(nombre))
    if crudo is None:
        return default
    return crudo.lower() in {"1", "true", "yes", "y", "on", "si"}
