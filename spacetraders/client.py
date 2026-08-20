"""Nucleo HTTP: rate limiting, reintentos, paginacion y desempaquetado de respuestas.

Todo endpoint de SpaceTraders responde con un sobre `{"data": ...}` y, en las
listas, tambien `{"meta": {"total", "page", "limit"}}`. `ApiClient` se encarga de
ese sobre, del token, del limite de 2 req/s y de los 429/5xx, para que la capa de
`spacetraders.api` solo hable de recursos del juego.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, TypeVar

import requests
from pydantic import BaseModel

from .config import Settings
from .errors import (
    ApiError,
    ServerError,
    TransportError,
    error_from_response,
)
from .ratelimit import RateLimiter

log = logging.getLogger("spacetraders.client")

M = TypeVar("M", bound=BaseModel)

# Metodos idempotentes: seguros de reintentar ante un fallo de red sin respuesta.
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Metodos donde un cuerpo ausente hay que mandarlo como `{}` (ver request_raw).
BODYLESS_NEEDS_EMPTY_JSON = frozenset({"POST", "PATCH", "PUT"})

MAX_BACKOFF_SECONDS = 30.0


class ApiClient:
    """Cliente HTTP de bajo nivel contra la API de SpaceTraders."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        token: str | None = None,
        limiter: RateLimiter | None = None,
        session: requests.Session | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        self.settings = settings or Settings()
        self.token = token
        self.limiter = limiter or RateLimiter()
        self._session = session or requests.Session()
        self._sleep = sleep
        # Segundos que el reloj del servidor le lleva al local (ver server_now).
        self._clock_skew = 0.0
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "moibe-spacetraders/0.2",
            }
        )

    # ------------------------------------------------------------------- reloj

    @property
    def clock_skew(self) -> float:
        """Desfase medido entre el reloj del servidor y el local, en segundos."""
        return self._clock_skew

    def server_now(self) -> datetime:
        """Hora estimada del servidor.

        En SpaceTraders todo esta cronometrado (llegadas, cooldowns, deadlines) y
        los tiempos vienen en la hora del servidor. Si el reloj local esta corrido
        -- unos minutos de deriva alcanzan -- restar `datetime.now()` de una hora
        de llegada da de menos y se le pregunta a la API antes de que la nave
        aterrice. Por eso se corrige con el desfase medido de la cabecera `Date`.
        """
        return datetime.now(UTC) + timedelta(seconds=self._clock_skew)

    def _actualizar_skew(self, respuesta: requests.Response) -> None:
        """Recalcula el desfase con la cabecera `Date` de cada respuesta."""
        fecha = respuesta.headers.get("Date")
        if not fecha:
            return
        try:
            hora_servidor = parsedate_to_datetime(fecha)
        except (TypeError, ValueError):
            return
        if hora_servidor.tzinfo is None:
            hora_servidor = hora_servidor.replace(tzinfo=UTC)

        anterior = self._clock_skew
        self._clock_skew = (hora_servidor - datetime.now(UTC)).total_seconds()
        # `Date` viene con resolucion de segundos, asi que +-1s es ruido normal.
        if abs(self._clock_skew - anterior) > 5:
            log.info(
                "reloj local desfasado %.0fs respecto al servidor; se corrigen las esperas",
                self._clock_skew,
            )

    # ------------------------------------------------------------------ tokens

    def set_token(self, token: str | None) -> None:
        """Fija el token de agente que firma las peticiones."""
        self.token = token

    def _auth_header(self, token_override: str | None) -> dict[str, str]:
        # `token=""` sirve para pedir explicitamente una peticion sin firmar.
        token = self.token if token_override is None else token_override
        return {"Authorization": f"Bearer {token}"} if token else {}

    # ----------------------------------------------------------------- request

    def request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ejecuta una peticion y devuelve el sobre JSON completo (`data` + `meta`).

        Reintenta 429 (respetando `Retry-After`), 5xx y fallos de red en metodos
        idempotentes. Cualquier otro 4xx sube como `ApiError` sin reintentar,
        porque reintentar un payload invalido no lo va a arreglar.
        """
        method = method.upper()
        url = f"{self.settings.base_url}{endpoint}"
        intentos = self.settings.max_retries + 1
        ultimo_error: Exception | None = None

        # Muchas acciones no llevan cuerpo (orbit, dock, accept, extract...), pero la
        # API rechaza con error 3001 un `Content-Type: application/json` con cuerpo
        # vacio: pide un objeto vacio explicito.
        if json is None and method in BODYLESS_NEEDS_EMPTY_JSON:
            json = {}

        for intento in range(1, intentos + 1):
            self.limiter.acquire()

            try:
                respuesta = self._session.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=self._auth_header(token),
                    timeout=self.settings.timeout,
                )
            except requests.exceptions.RequestException as exc:
                ultimo_error = TransportError(f"{method} {url} fallo: {exc}")
                # Sin respuesta no sabemos si el servidor aplico el cambio; solo se
                # reintenta lo idempotente para no duplicar compras o entregas.
                if method not in IDEMPOTENT_METHODS or intento == intentos:
                    raise ultimo_error from exc
                self._esperar_backoff(
                    intento, motivo=f"error de red ({exc.__class__.__name__})"
                )
                continue

            self._actualizar_skew(respuesta)
            payload = self._payload(respuesta)

            if respuesta.ok:
                return payload if isinstance(payload, dict) else {"data": payload}

            error = error_from_response(
                respuesta.status_code,
                payload if isinstance(payload, dict) else None,
                fallback=f"{method} {endpoint} devolvio HTTP {respuesta.status_code}",
            )

            if respuesta.status_code == 429:
                espera = self._espera_de_rate_limit(respuesta)
                self.limiter.penalize(espera)
                if intento == intentos:
                    raise error
                log.warning("429 en %s %s: esperando %.2fs", method, endpoint, espera)
                self._sleep(espera)
                ultimo_error = error
                continue

            if isinstance(error, ServerError):
                if intento == intentos:
                    raise error
                self._esperar_backoff(intento, motivo=f"HTTP {respuesta.status_code}")
                ultimo_error = error
                continue

            raise error

        # Solo se llega aca si se agotaron los intentos sin `raise` explicito.
        if isinstance(ultimo_error, Exception):
            raise ultimo_error
        raise ApiError(f"{method} {endpoint} se quedo sin reintentos", status=0)

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        token: str | None = None,
        model: type[M] | None = None,
    ) -> Any:
        """Como `request_raw`, pero devuelve solo `data`, opcionalmente ya parseado."""
        sobre = self.request_raw(method, endpoint, json=json, params=params, token=token)
        data = sobre.get("data")
        if model is not None:
            return model.model_validate(data)
        return data

    def get(self, endpoint: str, **kwargs: Any) -> Any:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs: Any) -> Any:
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs: Any) -> Any:
        return self.request("PATCH", endpoint, **kwargs)

    # -------------------------------------------------------------- paginacion

    def paginate(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        model: type[M] | None = None,
        limit: int = 20,
        max_pages: int | None = None,
    ) -> Iterator[Any]:
        """Recorre un endpoint paginado y va entregando elementos de a uno.

        Corta cuando `meta.total` dice que ya se vieron todos, cuando una pagina
        vuelve vacia, o al llegar a `max_pages` (util para no barrer 200k waypoints).
        """
        if not 1 <= limit <= 20:
            raise ValueError("limit debe estar entre 1 y 20 (tope de la API)")

        pagina = 1
        vistos = 0
        while True:
            consulta = dict(params or {})
            consulta.update({"page": pagina, "limit": limit})
            sobre = self.request_raw("GET", endpoint, params=consulta)

            items = sobre.get("data") or []
            if not items:
                return

            for item in items:
                yield model.model_validate(item) if model is not None else item
            vistos += len(items)

            meta = sobre.get("meta") or {}
            total = meta.get("total")
            if isinstance(total, int) and vistos >= total:
                return
            if max_pages is not None and pagina >= max_pages:
                log.debug("paginate corto en max_pages=%s para %s", max_pages, endpoint)
                return
            pagina += 1

    def list_all(self, endpoint: str, **kwargs: Any) -> list[Any]:
        """Version comoda de `paginate` que materializa la lista completa."""
        return list(self.paginate(endpoint, **kwargs))

    # ------------------------------------------------------------------ status

    def get_status(self) -> dict[str, Any]:
        """`GET /` -- estado del servidor. No requiere token.

        Trae `resetDate`, el proximo reset, estadisticas y leaderboards. Es la
        fuente de verdad para saber si el token guardado sigue sirviendo.
        """
        return self.request_raw("GET", "/", token="")

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _payload(respuesta: requests.Response) -> Any:
        """Decodifica el cuerpo como JSON, tolerando respuestas vacias o HTML."""
        if not respuesta.content:
            return None
        try:
            return respuesta.json()
        except ValueError:
            return {"error": {"message": respuesta.text[:500]}}

    def _espera_de_rate_limit(self, respuesta: requests.Response) -> float:
        """Cuanto esperar tras un 429, segun lo que diga la propia API."""
        retry_after = respuesta.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass

        reset = respuesta.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                momento = datetime.fromisoformat(reset.replace("Z", "+00:00"))
                # `X-RateLimit-Reset` viene en hora del servidor, no en la local.
                delta = (momento - self.server_now()).total_seconds()
                if delta > 0:
                    return min(delta, MAX_BACKOFF_SECONDS)
            except ValueError:
                pass

        return 1.0

    def _esperar_backoff(self, intento: int, *, motivo: str) -> None:
        """Backoff exponencial con jitter, para no sincronizar reintentos."""
        base = min(MAX_BACKOFF_SECONDS, 2.0 ** (intento - 1))
        espera = base * (0.5 + random.random() / 2)
        log.warning("reintento %s tras %s: esperando %.2fs", intento, motivo, espera)
        self._sleep(espera)

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
