"""Excepciones del cliente de SpaceTraders."""

from __future__ import annotations

from typing import Any


class SpaceTradersError(Exception):
    """Base de todos los errores del cliente."""


class ConfigError(SpaceTradersError):
    """Falta configuracion o es invalida (token de cuenta, simbolo de agente, etc.)."""


class ApiError(SpaceTradersError):
    """La API respondio con un error de negocio (4xx/5xx con cuerpo JSON)."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: int | None = None,
        data: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.data = data or {}
        self.request_id = request_id

    def __str__(self) -> str:
        partes = [f"HTTP {self.status}"]
        if self.code is not None:
            partes.append(f"code={self.code}")
        partes.append(self.message)
        if self.request_id:
            partes.append(f"(requestId={self.request_id})")
        return " ".join(partes)


class RateLimitError(ApiError):
    """429: se agoto el rate limit y se acabaron los reintentos."""


class UnauthorizedError(ApiError):
    """401: token ausente, invalido o vencido."""


class NotFoundError(ApiError):
    """404: el recurso no existe."""


class ServerError(ApiError):
    """5xx: la API fallo del lado del servidor."""


class TransportError(SpaceTradersError):
    """Fallo de red: no hubo respuesta HTTP (DNS, timeout, conexion cortada)."""


class ServerResetError(SpaceTradersError):
    """El universo se reseteo: el token guardado ya no sirve.

    La API se resetea semanalmente (sabados) e invalida todos los tokens de agente.
    `Session` lo detecta comparando el `resetDate` guardado contra el del endpoint
    de status, y re-registra el agente automaticamente si hay token de cuenta.
    """

    def __init__(self, stored_reset: str | None, current_reset: str) -> None:
        super().__init__(
            f"El servidor se reseteo (guardado={stored_reset!r}, actual={current_reset!r}). "
            "Hay que registrar el agente de nuevo."
        )
        self.stored_reset = stored_reset
        self.current_reset = current_reset


def error_from_response(
    status: int,
    payload: dict[str, Any] | None,
    fallback: str,
) -> ApiError:
    """Construye la excepcion adecuada a partir del cuerpo de error de la API.

    La API devuelve el error como
    `{"error": {"code": int, "message": str, "data": {...}, "requestId": str}}`.
    """
    error = (payload or {}).get("error")
    if not isinstance(error, dict):
        error = {}

    message = error.get("message") or fallback
    code = error.get("code") if isinstance(error.get("code"), int) else None
    data = error.get("data") if isinstance(error.get("data"), dict) else None
    request_id = error.get("requestId") if isinstance(error.get("requestId"), str) else None

    if status == 401:
        clase: type[ApiError] = UnauthorizedError
    elif status == 404:
        clase = NotFoundError
    elif status == 429:
        clase = RateLimitError
    elif status >= 500:
        clase = ServerError
    else:
        clase = ApiError

    return clase(message, status=status, code=code, data=data, request_id=request_id)
