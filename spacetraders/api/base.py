"""Base comun de las secciones de la API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..client import ApiClient


class ApiSection:
    """Agrupa endpoints relacionados sobre un `ApiClient` compartido."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client


def payload(modelo: BaseModel) -> dict[str, Any]:
    """Serializa un modelo para mandarlo a la API.

    `by_alias` devuelve las claves en camelCase como las espera el servidor y
    `mode="json"` convierte fechas y enums a algo serializable.
    """
    return modelo.model_dump(by_alias=True, mode="json", exclude_none=True)
