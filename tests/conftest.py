"""Utilidades compartidas por los tests."""

from __future__ import annotations

import json
from typing import Any

import pytest

from spacetraders.config import Settings


class RespuestaFalsa:
    """Imita lo que usa `ApiClient` de un `requests.Response`."""

    def __init__(
        self,
        status_code: int = 200,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = json.dumps(payload) if payload is not None else ""
        self.content = self.text.encode()

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("sin cuerpo JSON")
        return self._payload


class SesionFalsa:
    """Stub de `requests.Session` que devuelve respuestas programadas.

    Guarda cada llamada en `self.llamadas` para poder afirmar sobre el metodo, la
    URL, el cuerpo y las cabeceras que realmente se enviaron.
    """

    def __init__(self, respuestas: list[Any]) -> None:
        self.respuestas = list(respuestas)
        self.llamadas: list[dict[str, Any]] = []
        self.headers: dict[str, str] = {}
        self.cerrada = False

    def request(self, method: str, url: str, **kwargs: Any) -> RespuestaFalsa:
        self.llamadas.append({"method": method, "url": url, **kwargs})
        if not self.respuestas:
            raise AssertionError(f"llamada inesperada: {method} {url}")
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente

    def close(self) -> None:
        self.cerrada = True


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings aislados: sin red real ni tocar el token del usuario."""
    return Settings(
        account_token="cuenta-de-prueba",
        agent_symbol="TEST_AGENT",
        token_file=tmp_path / "agent.json",
        max_retries=2,
        timeout=1.0,
    )


@pytest.fixture
def sin_espera(monkeypatch):
    """Anula los sleeps para que los tests de reintento corran al instante."""
    esperas: list[float] = []
    monkeypatch.setattr("time.sleep", esperas.append)
    return esperas
