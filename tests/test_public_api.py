"""Tests de contrato contra la API real (endpoints publicos, sin token).

Sirven para detectar cuando la API cambia de forma bajo nuestros pies: es un juego
en alpha y el spec se mueve. No tocan el agente ni gastan creditos.

Se saltean con `-m "not network"` si no hay internet.
"""

from __future__ import annotations

import pytest

from spacetraders.client import ApiClient
from spacetraders.models import Faction, System

pytestmark = pytest.mark.network


@pytest.fixture(scope="module")
def cliente() -> ApiClient:
    c = ApiClient()
    yield c
    c.close()


def test_el_status_trae_la_temporada_y_el_proximo_reset(cliente):
    estado = cliente.get_status()

    assert "SpaceTraders" in estado["status"]
    assert estado["version"].startswith("v2")
    # `resetDate` es la clave de la que depende toda la logica de temporada.
    assert len(estado["resetDate"]) == 10
    assert estado["serverResets"]["frequency"]
    assert estado["stats"]["systems"] > 0


def test_las_facciones_parsean_al_modelo_generado(cliente):
    facciones = cliente.list_all("/factions", model=Faction)

    assert len(facciones) >= 10
    assert all(isinstance(f, Faction) for f in facciones)
    cosmic = next(f for f in facciones if str(f.symbol) == "COSMIC")
    assert cosmic.headquarters
    assert cosmic.traits


def test_la_paginacion_no_repite_ni_se_pasa(cliente):
    """Dos paginas de 5 sistemas: 10 simbolos distintos."""
    sistemas = list(cliente.paginate("/systems", model=System, limit=5, max_pages=2))

    assert len(sistemas) == 10
    assert len({s.symbol for s in sistemas}) == 10


def test_las_cabeceras_de_rate_limit_siguen_siendo_las_esperadas(cliente):
    """El limitador esta calibrado con estos numeros; si cambian, hay que ajustarlo."""
    import requests

    respuesta = requests.get(f"{cliente.settings.base_url}/factions", params={"limit": 1})

    assert respuesta.headers["X-RateLimit-Limit-Per-Second"] == "2"
    assert respuesta.headers["X-RateLimit-Limit-Burst"] == "30"
