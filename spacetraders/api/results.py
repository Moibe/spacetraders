"""Formas de respuesta de los endpoints que devuelven varios objetos a la vez.

Muchas acciones de SpaceTraders no devuelven una sola entidad: comprar carga
devuelve `agent` + `cargo` + `transaction`, y minar devuelve `cooldown` +
`extraction` + `cargo` + `events`. Estos modelos tipan esos sobres compuestos, con
los nombres exactos que usa la API (todos de una palabra, asi que no hacen falta
alias).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..models import (
    Agent,
    Chart,
    Construction,
    Contract,
    Cooldown,
    Extraction,
    MarketTransaction,
    RepairTransaction,
    ScannedShip,
    ScannedSystem,
    ScannedWaypoint,
    ScrapTransaction,
    Ship,
    ShipCargo,
    ShipConditionEvent,
    ShipFuel,
    ShipModificationTransaction,
    ShipModule,
    ShipMount,
    ShipNav,
    ShipyardTransaction,
    Siphon,
    Survey,
    TradeSymbol,
    Waypoint,
    WaypointModifier,
)

# --------------------------------------------------------------------- contratos


class ContractAgreement(BaseModel):
    """Resultado de aceptar o cumplir un contrato."""

    agent: Agent
    contract: Contract


class ContractDelivery(BaseModel):
    """Resultado de entregar mercancia de un contrato."""

    contract: Contract
    cargo: ShipCargo


# ------------------------------------------------------------------- navegacion


class NavigationResult(BaseModel):
    """Resultado de `navigate`, `warp` o de cambiar el modo de vuelo."""

    nav: ShipNav
    fuel: ShipFuel | None = None
    events: list[ShipConditionEvent] = Field(default_factory=list)


class JumpResult(BaseModel):
    """Resultado de un salto por jump gate (cobra creditos y deja cooldown)."""

    nav: ShipNav
    cooldown: Cooldown
    transaction: MarketTransaction | None = None
    agent: Agent | None = None


# ---------------------------------------------------------------------- mercado


class MarketOperation(BaseModel):
    """Resultado de comprar o vender carga en un mercado."""

    agent: Agent
    cargo: ShipCargo
    transaction: MarketTransaction


class RefuelResult(BaseModel):
    """Resultado de recargar combustible."""

    agent: Agent
    fuel: ShipFuel
    transaction: MarketTransaction
    cargo: ShipCargo | None = None


class ShipPurchase(BaseModel):
    """Resultado de comprar una nave en un astillero."""

    agent: Agent
    ship: Ship
    transaction: ShipyardTransaction


# ------------------------------------------------------------ mineria y refinado


class ExtractionResult(BaseModel):
    """Resultado de minar un asteroide (con o sin survey)."""

    cooldown: Cooldown
    extraction: Extraction
    cargo: ShipCargo
    modifiers: list[WaypointModifier] = Field(default_factory=list)
    events: list[ShipConditionEvent] = Field(default_factory=list)


class SiphonResult(BaseModel):
    """Resultado de sifonear gas de un gigante gaseoso."""

    cooldown: Cooldown
    siphon: Siphon
    cargo: ShipCargo
    events: list[ShipConditionEvent] = Field(default_factory=list)


class SurveyResult(BaseModel):
    """Resultado de mapear depositos en un waypoint minable."""

    cooldown: Cooldown
    surveys: list[Survey]


class RefinedGood(BaseModel):
    """Renglon de mercancia producida o consumida al refinar."""

    trade_symbol: TradeSymbol | str | None = None
    units: int | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class RefineResult(BaseModel):
    """Resultado de refinar mineral en bruto a bordo."""

    cargo: ShipCargo
    cooldown: Cooldown
    produced: list[RefinedGood] = Field(default_factory=list)
    consumed: list[RefinedGood] = Field(default_factory=list)


# ----------------------------------------------------------- escaneo y cartografia


class ChartResult(BaseModel):
    """Resultado de cartografiar un waypoint sin mapear."""

    chart: Chart
    waypoint: Waypoint
    agent: Agent | None = None


class SystemScan(BaseModel):
    cooldown: Cooldown
    systems: list[ScannedSystem]


class WaypointScan(BaseModel):
    cooldown: Cooldown
    waypoints: list[ScannedWaypoint]


class ShipScan(BaseModel):
    cooldown: Cooldown
    ships: list[ScannedShip]


# ---------------------------------------------------------- modificaciones de nave


class MountChange(BaseModel):
    """Resultado de instalar o quitar un mount."""

    agent: Agent
    mounts: list[ShipMount]
    cargo: ShipCargo
    transaction: ShipModificationTransaction | None = None


class ModuleChange(BaseModel):
    """Resultado de instalar o quitar un modulo."""

    agent: Agent
    modules: list[ShipModule]
    cargo: ShipCargo
    transaction: dict | None = None


class RepairResult(BaseModel):
    agent: Agent
    ship: Ship
    transaction: RepairTransaction


class ScrapResult(BaseModel):
    agent: Agent
    transaction: ScrapTransaction


# ------------------------------------------------------------------ construccion


class ConstructionSupply(BaseModel):
    """Resultado de aportar materiales a una construccion (jump gate, etc.)."""

    construction: Construction
    cargo: ShipCargo
