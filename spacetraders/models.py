"""Modelos de la API de SpaceTraders (v2.3.0).

ARCHIVO GENERADO -- no editar a mano.
Se genera desde el OpenAPI oficial (github.com/SpaceTradersAPI/api-docs) con:

    python tools/generate_models.py

Los campos usan snake_case en Python y alias camelCase para la API, asi que al
serializar hacia la API hay que usar `.model_dump(by_alias=True)`.
"""

from __future__ import annotations
from enum import StrEnum
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    confloat,
    conint,
    constr,
)


class ActivityLevel(StrEnum):
    """
    The activity level of a trade good. If the good is an import, this represents how strong consumption is. If the good is an export, this represents how strong the production is for the good. When activity is strong, consumption or production is near maximum capacity. When activity is weak, consumption or production is near minimum capacity.
    """

    weak = 'WEAK'
    growing = 'GROWING'
    strong = 'STRONG'
    restricted = 'RESTRICTED'


class Agent(BaseModel):
    """
    Agent details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    account_id: constr(min_length=1) | None = Field(
        None,
        alias='accountId',
        description='Account ID that is tied to this agent. Only included on your own agent.',
    )
    symbol: constr(min_length=3, max_length=14) = Field(
        ..., description='Symbol of the agent.'
    )
    headquarters: constr(min_length=1) = Field(
        ..., description='The headquarters of the agent.'
    )
    credits: int = Field(
        ...,
        description='The number of credits the agent has available. Credits can be negative if funds have been overdrawn.',
    )
    starting_faction: constr(min_length=1) = Field(
        ..., alias='startingFaction', description='The faction the agent started with.'
    )
    ship_count: int = Field(
        ..., alias='shipCount', description='How many ships are owned by the agent.'
    )


class Type(StrEnum):
    """
    Type of contract.
    """

    procurement = 'PROCUREMENT'
    transport = 'TRANSPORT'
    shuttle = 'SHUTTLE'


class ContractDeliverGood(BaseModel):
    """
    The details of a delivery contract. Includes the type of good, units needed, and the destination.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    trade_symbol: constr(min_length=1) = Field(
        ..., alias='tradeSymbol', description='The symbol of the trade good to deliver.'
    )
    destination_symbol: constr(min_length=1) = Field(
        ...,
        alias='destinationSymbol',
        description='The destination where goods need to be delivered.',
    )
    units_required: int = Field(
        ...,
        alias='unitsRequired',
        description='The number of units that need to be delivered on this contract.',
    )
    units_fulfilled: int = Field(
        ...,
        alias='unitsFulfilled',
        description='The number of units fulfilled on this contract.',
    )


class ContractPayment(BaseModel):
    """
    Payments for the contract.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    on_accepted: int = Field(
        ...,
        alias='onAccepted',
        description='The amount of credits received up front for accepting the contract.',
    )
    on_fulfilled: int = Field(
        ...,
        alias='onFulfilled',
        description='The amount of credits received when the contract is fulfilled.',
    )


class ContractTerms(BaseModel):
    """
    The terms to fulfill the contract.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    deadline: AwareDatetime = Field(..., description='The deadline for the contract.')
    payment: ContractPayment
    deliver: list[ContractDeliverGood] | None = Field(
        None,
        description='The cargo that needs to be delivered to fulfill the contract.',
    )


class Cooldown(BaseModel):
    """
    A cooldown is a period of time in which a ship cannot perform certain actions.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    ship_symbol: constr(min_length=1) = Field(
        ...,
        alias='shipSymbol',
        description='The symbol of the ship that is on cooldown',
    )
    total_seconds: conint(ge=0) = Field(
        ...,
        alias='totalSeconds',
        description='The total duration of the cooldown in seconds',
    )
    remaining_seconds: conint(ge=0) = Field(
        ...,
        alias='remainingSeconds',
        description='The remaining duration of the cooldown in seconds',
    )
    expiration: AwareDatetime | None = Field(
        None,
        description='The date and time when the cooldown expires in ISO 8601 format',
    )


class FactionSymbol(StrEnum):
    """
    The symbol of the faction.
    """

    cosmic = 'COSMIC'
    void = 'VOID'
    galactic = 'GALACTIC'
    quantum = 'QUANTUM'
    dominion = 'DOMINION'
    astro = 'ASTRO'
    corsairs = 'CORSAIRS'
    obsidian = 'OBSIDIAN'
    aegis = 'AEGIS'
    united = 'UNITED'
    solitary = 'SOLITARY'
    cobalt = 'COBALT'
    omega = 'OMEGA'
    echo = 'ECHO'
    lords = 'LORDS'
    cult = 'CULT'
    ancients = 'ANCIENTS'
    shadow = 'SHADOW'
    ethereal = 'ETHEREAL'


class FactionTraitSymbol(StrEnum):
    """
    The unique identifier of the trait.
    """

    bureaucratic = 'BUREAUCRATIC'
    secretive = 'SECRETIVE'
    capitalistic = 'CAPITALISTIC'
    industrious = 'INDUSTRIOUS'
    peaceful = 'PEACEFUL'
    distrustful = 'DISTRUSTFUL'
    welcoming = 'WELCOMING'
    smugglers = 'SMUGGLERS'
    scavengers = 'SCAVENGERS'
    rebellious = 'REBELLIOUS'
    exiles = 'EXILES'
    pirates = 'PIRATES'
    raiders = 'RAIDERS'
    clan = 'CLAN'
    guild = 'GUILD'
    dominion = 'DOMINION'
    fringe = 'FRINGE'
    forsaken = 'FORSAKEN'
    isolated = 'ISOLATED'
    localized = 'LOCALIZED'
    established = 'ESTABLISHED'
    notable = 'NOTABLE'
    dominant = 'DOMINANT'
    inescapable = 'INESCAPABLE'
    innovative = 'INNOVATIVE'
    bold = 'BOLD'
    visionary = 'VISIONARY'
    curious = 'CURIOUS'
    daring = 'DARING'
    exploratory = 'EXPLORATORY'
    resourceful = 'RESOURCEFUL'
    flexible = 'FLEXIBLE'
    cooperative = 'COOPERATIVE'
    united = 'UNITED'
    strategic = 'STRATEGIC'
    intelligent = 'INTELLIGENT'
    research_focused = 'RESEARCH_FOCUSED'
    collaborative = 'COLLABORATIVE'
    progressive = 'PROGRESSIVE'
    militaristic = 'MILITARISTIC'
    technologically_advanced = 'TECHNOLOGICALLY_ADVANCED'
    aggressive = 'AGGRESSIVE'
    imperialistic = 'IMPERIALISTIC'
    treasure_hunters = 'TREASURE_HUNTERS'
    dexterous = 'DEXTEROUS'
    unpredictable = 'UNPREDICTABLE'
    brutal = 'BRUTAL'
    fleeting = 'FLEETING'
    adaptable = 'ADAPTABLE'
    self_sufficient = 'SELF_SUFFICIENT'
    defensive = 'DEFENSIVE'
    proud = 'PROUD'
    diverse = 'DIVERSE'
    independent = 'INDEPENDENT'
    self_interested = 'SELF_INTERESTED'
    fragmented = 'FRAGMENTED'
    commercial = 'COMMERCIAL'
    free_markets = 'FREE_MARKETS'
    entrepreneurial = 'ENTREPRENEURIAL'


class Type1(StrEnum):
    """
    The type of trade good (export, import, or exchange).
    """

    export = 'EXPORT'
    import_ = 'IMPORT'
    exchange = 'EXCHANGE'


class Type2(StrEnum):
    """
    The type of transaction.
    """

    purchase = 'PURCHASE'
    sell = 'SELL'


class Meta(BaseModel):
    """
    Meta details for pagination.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    total: conint(ge=0) = Field(
        ..., description='Shows the total amount of items of this kind that exist.'
    )
    page: conint(ge=1) = Field(
        ...,
        description='A page denotes an amount of items, offset from the first item. Each page holds an amount of items equal to the `limit`.',
    )
    limit: conint(ge=1, le=20) = Field(
        ...,
        description='The amount of items in each page. Limits how many items can be fetched at once.',
    )


class Frame(BaseModel):
    """
    The frame of the ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The symbol of the frame.')


class Reactor(BaseModel):
    """
    The reactor of the ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The symbol of the reactor.')


class Engine(BaseModel):
    """
    The engine of the ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The symbol of the engine.')


class Mount(BaseModel):
    """
    A mount on the ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The symbol of the mount.')


class Symbol(StrEnum):
    reactor_overload = 'REACTOR_OVERLOAD'
    energy_spike_from_mineral = 'ENERGY_SPIKE_FROM_MINERAL'
    solar_flare_interference = 'SOLAR_FLARE_INTERFERENCE'
    coolant_leak = 'COOLANT_LEAK'
    power_distribution_fluctuation = 'POWER_DISTRIBUTION_FLUCTUATION'
    magnetic_field_disruption = 'MAGNETIC_FIELD_DISRUPTION'
    hull_micrometeorite_strikes = 'HULL_MICROMETEORITE_STRIKES'
    structural_stress_fractures = 'STRUCTURAL_STRESS_FRACTURES'
    corrosive_mineral_contamination = 'CORROSIVE_MINERAL_CONTAMINATION'
    thermal_expansion_mismatch = 'THERMAL_EXPANSION_MISMATCH'
    vibration_damage_from_drilling = 'VIBRATION_DAMAGE_FROM_DRILLING'
    electromagnetic_field_interference = 'ELECTROMAGNETIC_FIELD_INTERFERENCE'
    impact_with_extracted_debris = 'IMPACT_WITH_EXTRACTED_DEBRIS'
    fuel_efficiency_degradation = 'FUEL_EFFICIENCY_DEGRADATION'
    coolant_system_ageing = 'COOLANT_SYSTEM_AGEING'
    dust_microabrasions = 'DUST_MICROABRASIONS'
    thruster_nozzle_wear = 'THRUSTER_NOZZLE_WEAR'
    exhaust_port_clogging = 'EXHAUST_PORT_CLOGGING'
    bearing_lubrication_fade = 'BEARING_LUBRICATION_FADE'
    sensor_calibration_drift = 'SENSOR_CALIBRATION_DRIFT'
    hull_micrometeorite_damage = 'HULL_MICROMETEORITE_DAMAGE'
    space_debris_collision = 'SPACE_DEBRIS_COLLISION'
    thermal_stress = 'THERMAL_STRESS'
    vibration_overload = 'VIBRATION_OVERLOAD'
    pressure_differential_stress = 'PRESSURE_DIFFERENTIAL_STRESS'
    electromagnetic_surge_effects = 'ELECTROMAGNETIC_SURGE_EFFECTS'
    atmospheric_entry_heat = 'ATMOSPHERIC_ENTRY_HEAT'


class Component(StrEnum):
    frame = 'FRAME'
    reactor = 'REACTOR'
    engine = 'ENGINE'


class ShipConditionEvent(BaseModel):
    """
    An event that represents damage or wear to a ship's reactor, frame, or engine, reducing the condition of the ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: Symbol
    component: Component
    name: str = Field(..., description='The name of the event.')
    description: str = Field(..., description='A description of the event.')


class Rotation(StrEnum):
    """
    The rotation of crew shifts. A stricter shift improves the ship's performance. A more relaxed shift improves the crew's morale.
    """

    strict = 'STRICT'
    relaxed = 'RELAXED'


class ShipCrew(BaseModel):
    """
    The ship's crew service and maintain the ship's systems and equipment.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    current: int = Field(
        ..., description='The current number of crew members on the ship.'
    )
    required: int = Field(
        ...,
        description='The minimum number of crew members required to maintain the ship.',
    )
    capacity: int = Field(
        ..., description='The maximum number of crew members the ship can support.'
    )
    rotation: Rotation = Field(
        ...,
        description="The rotation of crew shifts. A stricter shift improves the ship's performance. A more relaxed shift improves the crew's morale.",
    )
    morale: conint(ge=0, le=100) = Field(
        ...,
        description="A rough measure of the crew's morale. A higher morale means the crew is happier and more productive. A lower morale means the ship is more prone to accidents.",
    )
    wages: conint(ge=0) = Field(
        ...,
        description='The amount of credits per crew member paid per hour. Wages are paid when a ship docks at a civilized waypoint.',
    )


class Symbol1(StrEnum):
    """
    The symbol of the engine.
    """

    engine_impulse_drive_i = 'ENGINE_IMPULSE_DRIVE_I'
    engine_ion_drive_i = 'ENGINE_ION_DRIVE_I'
    engine_ion_drive_ii = 'ENGINE_ION_DRIVE_II'
    engine_hyper_drive_i = 'ENGINE_HYPER_DRIVE_I'


class Symbol2(StrEnum):
    """
    Symbol of the frame.
    """

    frame_probe = 'FRAME_PROBE'
    frame_drone = 'FRAME_DRONE'
    frame_interceptor = 'FRAME_INTERCEPTOR'
    frame_racer = 'FRAME_RACER'
    frame_fighter = 'FRAME_FIGHTER'
    frame_frigate = 'FRAME_FRIGATE'
    frame_shuttle = 'FRAME_SHUTTLE'
    frame_explorer = 'FRAME_EXPLORER'
    frame_miner = 'FRAME_MINER'
    frame_light_freighter = 'FRAME_LIGHT_FREIGHTER'
    frame_heavy_freighter = 'FRAME_HEAVY_FREIGHTER'
    frame_transport = 'FRAME_TRANSPORT'
    frame_destroyer = 'FRAME_DESTROYER'
    frame_cruiser = 'FRAME_CRUISER'
    frame_carrier = 'FRAME_CARRIER'
    frame_bulk_freighter = 'FRAME_BULK_FREIGHTER'


class Consumed(BaseModel):
    """
    An object that only shows up when an action has consumed fuel in the process. Shows the fuel consumption data.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    amount: conint(ge=0) = Field(
        ...,
        description='The amount of fuel consumed by the most recent transit or action.',
    )
    timestamp: AwareDatetime = Field(
        ..., description='The time at which the fuel was consumed.'
    )


class ShipFuel(BaseModel):
    """
    Details of the ship's fuel tanks including how much fuel was consumed during the last transit or action.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    current: conint(ge=0) = Field(
        ..., description="The current amount of fuel in the ship's tanks."
    )
    capacity: conint(ge=0) = Field(
        ..., description="The maximum amount of fuel the ship's tanks can hold."
    )
    consumed: Consumed | None = Field(
        None,
        description='An object that only shows up when an action has consumed fuel in the process. Shows the fuel consumption data.',
    )


class ShipModificationTransaction(BaseModel):
    """
    Result of a transaction for a ship modification, such as installing a mount or a module.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    waypoint_symbol: str = Field(
        ...,
        alias='waypointSymbol',
        description='The symbol of the waypoint where the transaction took place.',
    )
    ship_symbol: str = Field(
        ...,
        alias='shipSymbol',
        description='The symbol of the ship that made the transaction.',
    )
    trade_symbol: str = Field(
        ..., alias='tradeSymbol', description='The symbol of the trade good.'
    )
    total_price: conint(ge=0) = Field(
        ..., alias='totalPrice', description='The total price of the transaction.'
    )
    timestamp: AwareDatetime = Field(
        ..., description='The timestamp of the transaction.'
    )


class Symbol3(StrEnum):
    """
    The symbol of the module.
    """

    module_mineral_processor_i = 'MODULE_MINERAL_PROCESSOR_I'
    module_gas_processor_i = 'MODULE_GAS_PROCESSOR_I'
    module_cargo_hold_i = 'MODULE_CARGO_HOLD_I'
    module_cargo_hold_ii = 'MODULE_CARGO_HOLD_II'
    module_cargo_hold_iii = 'MODULE_CARGO_HOLD_III'
    module_crew_quarters_i = 'MODULE_CREW_QUARTERS_I'
    module_envoy_quarters_i = 'MODULE_ENVOY_QUARTERS_I'
    module_passenger_cabin_i = 'MODULE_PASSENGER_CABIN_I'
    module_micro_refinery_i = 'MODULE_MICRO_REFINERY_I'
    module_ore_refinery_i = 'MODULE_ORE_REFINERY_I'
    module_fuel_refinery_i = 'MODULE_FUEL_REFINERY_I'
    module_science_lab_i = 'MODULE_SCIENCE_LAB_I'
    module_jump_drive_i = 'MODULE_JUMP_DRIVE_I'
    module_jump_drive_ii = 'MODULE_JUMP_DRIVE_II'
    module_jump_drive_iii = 'MODULE_JUMP_DRIVE_III'
    module_warp_drive_i = 'MODULE_WARP_DRIVE_I'
    module_warp_drive_ii = 'MODULE_WARP_DRIVE_II'
    module_warp_drive_iii = 'MODULE_WARP_DRIVE_III'
    module_shield_generator_i = 'MODULE_SHIELD_GENERATOR_I'
    module_shield_generator_ii = 'MODULE_SHIELD_GENERATOR_II'


class Symbol4(StrEnum):
    """
    Symbo of this mount.
    """

    mount_gas_siphon_i = 'MOUNT_GAS_SIPHON_I'
    mount_gas_siphon_ii = 'MOUNT_GAS_SIPHON_II'
    mount_gas_siphon_iii = 'MOUNT_GAS_SIPHON_III'
    mount_surveyor_i = 'MOUNT_SURVEYOR_I'
    mount_surveyor_ii = 'MOUNT_SURVEYOR_II'
    mount_surveyor_iii = 'MOUNT_SURVEYOR_III'
    mount_sensor_array_i = 'MOUNT_SENSOR_ARRAY_I'
    mount_sensor_array_ii = 'MOUNT_SENSOR_ARRAY_II'
    mount_sensor_array_iii = 'MOUNT_SENSOR_ARRAY_III'
    mount_mining_laser_i = 'MOUNT_MINING_LASER_I'
    mount_mining_laser_ii = 'MOUNT_MINING_LASER_II'
    mount_mining_laser_iii = 'MOUNT_MINING_LASER_III'
    mount_laser_cannon_i = 'MOUNT_LASER_CANNON_I'
    mount_missile_launcher_i = 'MOUNT_MISSILE_LAUNCHER_I'
    mount_turret_i = 'MOUNT_TURRET_I'


class Deposit(StrEnum):
    quartz_sand = 'QUARTZ_SAND'
    silicon_crystals = 'SILICON_CRYSTALS'
    precious_stones = 'PRECIOUS_STONES'
    ice_water = 'ICE_WATER'
    ammonia_ice = 'AMMONIA_ICE'
    iron_ore = 'IRON_ORE'
    copper_ore = 'COPPER_ORE'
    silver_ore = 'SILVER_ORE'
    aluminum_ore = 'ALUMINUM_ORE'
    gold_ore = 'GOLD_ORE'
    platinum_ore = 'PLATINUM_ORE'
    diamonds = 'DIAMONDS'
    uranite_ore = 'URANITE_ORE'
    meritium_ore = 'MERITIUM_ORE'


class ShipNavFlightMode(StrEnum):
    """
    The ship's set speed when traveling between waypoints or systems.
    """

    drift = 'DRIFT'
    stealth = 'STEALTH'
    cruise = 'CRUISE'
    burn = 'BURN'


class ShipNavStatus(StrEnum):
    """
    The current status of the ship
    """

    in_transit = 'IN_TRANSIT'
    in_orbit = 'IN_ORBIT'
    docked = 'DOCKED'


class Symbol5(StrEnum):
    """
    Symbol of the reactor.
    """

    reactor_solar_i = 'REACTOR_SOLAR_I'
    reactor_fusion_i = 'REACTOR_FUSION_I'
    reactor_fission_i = 'REACTOR_FISSION_I'
    reactor_chemical_i = 'REACTOR_CHEMICAL_I'
    reactor_antimatter_i = 'REACTOR_ANTIMATTER_I'


class ShipRequirements(BaseModel):
    """
    The requirements for installation on a ship
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    power: int | None = Field(
        None, description='The amount of power required from the reactor.'
    )
    crew: int | None = Field(
        None, description='The number of crew required for operation.'
    )
    slots: int | None = Field(
        None, description='The number of module slots required for installation.'
    )


class ShipRole(StrEnum):
    """
    The registered role of the ship
    """

    fabricator = 'FABRICATOR'
    harvester = 'HARVESTER'
    hauler = 'HAULER'
    interceptor = 'INTERCEPTOR'
    excavator = 'EXCAVATOR'
    transport = 'TRANSPORT'
    repair = 'REPAIR'
    surveyor = 'SURVEYOR'
    command = 'COMMAND'
    carrier = 'CARRIER'
    patrol = 'PATROL'
    satellite = 'SATELLITE'
    explorer = 'EXPLORER'
    refinery = 'REFINERY'


class ShipType(StrEnum):
    """
    Type of ship
    """

    ship_probe = 'SHIP_PROBE'
    ship_mining_drone = 'SHIP_MINING_DRONE'
    ship_siphon_drone = 'SHIP_SIPHON_DRONE'
    ship_interceptor = 'SHIP_INTERCEPTOR'
    ship_light_hauler = 'SHIP_LIGHT_HAULER'
    ship_command_frigate = 'SHIP_COMMAND_FRIGATE'
    ship_explorer = 'SHIP_EXPLORER'
    ship_heavy_freighter = 'SHIP_HEAVY_FREIGHTER'
    ship_light_shuttle = 'SHIP_LIGHT_SHUTTLE'
    ship_ore_hound = 'SHIP_ORE_HOUND'
    ship_refining_freighter = 'SHIP_REFINING_FREIGHTER'
    ship_surveyor = 'SHIP_SURVEYOR'
    ship_bulk_freighter = 'SHIP_BULK_FREIGHTER'


class ShipType1(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: ShipType


class Crew(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    required: int
    capacity: int


class SupplyLevel(StrEnum):
    """
    The supply level of a trade good.
    """

    scarce = 'SCARCE'
    limited = 'LIMITED'
    moderate = 'MODERATE'
    high = 'HIGH'
    abundant = 'ABUNDANT'


class Size(StrEnum):
    """
    The size of the deposit. This value indicates how much can be extracted from the survey before it is exhausted.
    """

    small = 'SMALL'
    moderate = 'MODERATE'
    large = 'LARGE'


class SurveyDeposit(BaseModel):
    """
    A surveyed deposit of a mineral or resource available for extraction.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The symbol of the deposit.')


class SystemFaction(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: FactionSymbol


class SystemType(StrEnum):
    """
    The type of system.
    """

    neutron_star = 'NEUTRON_STAR'
    red_star = 'RED_STAR'
    orange_star = 'ORANGE_STAR'
    blue_star = 'BLUE_STAR'
    young_star = 'YOUNG_STAR'
    white_dwarf = 'WHITE_DWARF'
    black_hole = 'BLACK_HOLE'
    hypergiant = 'HYPERGIANT'
    nebula = 'NEBULA'
    unstable = 'UNSTABLE'


class TradeSymbol(StrEnum):
    """
    The good's symbol.
    """

    precious_stones = 'PRECIOUS_STONES'
    quartz_sand = 'QUARTZ_SAND'
    silicon_crystals = 'SILICON_CRYSTALS'
    ammonia_ice = 'AMMONIA_ICE'
    liquid_hydrogen = 'LIQUID_HYDROGEN'
    liquid_nitrogen = 'LIQUID_NITROGEN'
    ice_water = 'ICE_WATER'
    exotic_matter = 'EXOTIC_MATTER'
    advanced_circuitry = 'ADVANCED_CIRCUITRY'
    graviton_emitters = 'GRAVITON_EMITTERS'
    iron = 'IRON'
    iron_ore = 'IRON_ORE'
    copper = 'COPPER'
    copper_ore = 'COPPER_ORE'
    aluminum = 'ALUMINUM'
    aluminum_ore = 'ALUMINUM_ORE'
    silver = 'SILVER'
    silver_ore = 'SILVER_ORE'
    gold = 'GOLD'
    gold_ore = 'GOLD_ORE'
    platinum = 'PLATINUM'
    platinum_ore = 'PLATINUM_ORE'
    diamonds = 'DIAMONDS'
    uranite = 'URANITE'
    uranite_ore = 'URANITE_ORE'
    meritium = 'MERITIUM'
    meritium_ore = 'MERITIUM_ORE'
    hydrocarbon = 'HYDROCARBON'
    antimatter = 'ANTIMATTER'
    fab_mats = 'FAB_MATS'
    fertilizers = 'FERTILIZERS'
    fabrics = 'FABRICS'
    food = 'FOOD'
    jewelry = 'JEWELRY'
    machinery = 'MACHINERY'
    firearms = 'FIREARMS'
    assault_rifles = 'ASSAULT_RIFLES'
    military_equipment = 'MILITARY_EQUIPMENT'
    explosives = 'EXPLOSIVES'
    lab_instruments = 'LAB_INSTRUMENTS'
    ammunition = 'AMMUNITION'
    electronics = 'ELECTRONICS'
    ship_plating = 'SHIP_PLATING'
    ship_parts = 'SHIP_PARTS'
    equipment = 'EQUIPMENT'
    fuel = 'FUEL'
    medicine = 'MEDICINE'
    drugs = 'DRUGS'
    clothing = 'CLOTHING'
    microprocessors = 'MICROPROCESSORS'
    plastics = 'PLASTICS'
    polynucleotides = 'POLYNUCLEOTIDES'
    biocomposites = 'BIOCOMPOSITES'
    quantum_stabilizers = 'QUANTUM_STABILIZERS'
    nanobots = 'NANOBOTS'
    ai_mainframes = 'AI_MAINFRAMES'
    quantum_drives = 'QUANTUM_DRIVES'
    robotic_drones = 'ROBOTIC_DRONES'
    cyber_implants = 'CYBER_IMPLANTS'
    gene_therapeutics = 'GENE_THERAPEUTICS'
    neural_chips = 'NEURAL_CHIPS'
    mood_regulators = 'MOOD_REGULATORS'
    viral_agents = 'VIRAL_AGENTS'
    micro_fusion_generators = 'MICRO_FUSION_GENERATORS'
    supergrains = 'SUPERGRAINS'
    laser_rifles = 'LASER_RIFLES'
    holographics = 'HOLOGRAPHICS'
    ship_salvage = 'SHIP_SALVAGE'
    relic_tech = 'RELIC_TECH'
    novel_lifeforms = 'NOVEL_LIFEFORMS'
    botanical_specimens = 'BOTANICAL_SPECIMENS'
    cultural_artifacts = 'CULTURAL_ARTIFACTS'
    frame_probe = 'FRAME_PROBE'
    frame_drone = 'FRAME_DRONE'
    frame_interceptor = 'FRAME_INTERCEPTOR'
    frame_racer = 'FRAME_RACER'
    frame_fighter = 'FRAME_FIGHTER'
    frame_frigate = 'FRAME_FRIGATE'
    frame_shuttle = 'FRAME_SHUTTLE'
    frame_explorer = 'FRAME_EXPLORER'
    frame_miner = 'FRAME_MINER'
    frame_light_freighter = 'FRAME_LIGHT_FREIGHTER'
    frame_heavy_freighter = 'FRAME_HEAVY_FREIGHTER'
    frame_transport = 'FRAME_TRANSPORT'
    frame_destroyer = 'FRAME_DESTROYER'
    frame_cruiser = 'FRAME_CRUISER'
    frame_carrier = 'FRAME_CARRIER'
    frame_bulk_freighter = 'FRAME_BULK_FREIGHTER'
    reactor_solar_i = 'REACTOR_SOLAR_I'
    reactor_fusion_i = 'REACTOR_FUSION_I'
    reactor_fission_i = 'REACTOR_FISSION_I'
    reactor_chemical_i = 'REACTOR_CHEMICAL_I'
    reactor_antimatter_i = 'REACTOR_ANTIMATTER_I'
    engine_impulse_drive_i = 'ENGINE_IMPULSE_DRIVE_I'
    engine_ion_drive_i = 'ENGINE_ION_DRIVE_I'
    engine_ion_drive_ii = 'ENGINE_ION_DRIVE_II'
    engine_hyper_drive_i = 'ENGINE_HYPER_DRIVE_I'
    module_mineral_processor_i = 'MODULE_MINERAL_PROCESSOR_I'
    module_gas_processor_i = 'MODULE_GAS_PROCESSOR_I'
    module_cargo_hold_i = 'MODULE_CARGO_HOLD_I'
    module_cargo_hold_ii = 'MODULE_CARGO_HOLD_II'
    module_cargo_hold_iii = 'MODULE_CARGO_HOLD_III'
    module_crew_quarters_i = 'MODULE_CREW_QUARTERS_I'
    module_envoy_quarters_i = 'MODULE_ENVOY_QUARTERS_I'
    module_passenger_cabin_i = 'MODULE_PASSENGER_CABIN_I'
    module_micro_refinery_i = 'MODULE_MICRO_REFINERY_I'
    module_science_lab_i = 'MODULE_SCIENCE_LAB_I'
    module_jump_drive_i = 'MODULE_JUMP_DRIVE_I'
    module_jump_drive_ii = 'MODULE_JUMP_DRIVE_II'
    module_jump_drive_iii = 'MODULE_JUMP_DRIVE_III'
    module_warp_drive_i = 'MODULE_WARP_DRIVE_I'
    module_warp_drive_ii = 'MODULE_WARP_DRIVE_II'
    module_warp_drive_iii = 'MODULE_WARP_DRIVE_III'
    module_shield_generator_i = 'MODULE_SHIELD_GENERATOR_I'
    module_shield_generator_ii = 'MODULE_SHIELD_GENERATOR_II'
    module_ore_refinery_i = 'MODULE_ORE_REFINERY_I'
    module_fuel_refinery_i = 'MODULE_FUEL_REFINERY_I'
    mount_gas_siphon_i = 'MOUNT_GAS_SIPHON_I'
    mount_gas_siphon_ii = 'MOUNT_GAS_SIPHON_II'
    mount_gas_siphon_iii = 'MOUNT_GAS_SIPHON_III'
    mount_surveyor_i = 'MOUNT_SURVEYOR_I'
    mount_surveyor_ii = 'MOUNT_SURVEYOR_II'
    mount_surveyor_iii = 'MOUNT_SURVEYOR_III'
    mount_sensor_array_i = 'MOUNT_SENSOR_ARRAY_I'
    mount_sensor_array_ii = 'MOUNT_SENSOR_ARRAY_II'
    mount_sensor_array_iii = 'MOUNT_SENSOR_ARRAY_III'
    mount_mining_laser_i = 'MOUNT_MINING_LASER_I'
    mount_mining_laser_ii = 'MOUNT_MINING_LASER_II'
    mount_mining_laser_iii = 'MOUNT_MINING_LASER_III'
    mount_laser_cannon_i = 'MOUNT_LASER_CANNON_I'
    mount_missile_launcher_i = 'MOUNT_MISSILE_LAUNCHER_I'
    mount_turret_i = 'MOUNT_TURRET_I'
    ship_probe = 'SHIP_PROBE'
    ship_mining_drone = 'SHIP_MINING_DRONE'
    ship_siphon_drone = 'SHIP_SIPHON_DRONE'
    ship_interceptor = 'SHIP_INTERCEPTOR'
    ship_light_hauler = 'SHIP_LIGHT_HAULER'
    ship_command_frigate = 'SHIP_COMMAND_FRIGATE'
    ship_explorer = 'SHIP_EXPLORER'
    ship_heavy_freighter = 'SHIP_HEAVY_FREIGHTER'
    ship_light_shuttle = 'SHIP_LIGHT_SHUTTLE'
    ship_ore_hound = 'SHIP_ORE_HOUND'
    ship_refining_freighter = 'SHIP_REFINING_FREIGHTER'
    ship_surveyor = 'SHIP_SURVEYOR'
    ship_bulk_freighter = 'SHIP_BULK_FREIGHTER'


class WaypointFaction(BaseModel):
    """
    The faction that controls the waypoint.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: FactionSymbol


class WaypointModifierSymbol(StrEnum):
    """
    The unique identifier of the modifier.
    """

    stripped = 'STRIPPED'
    unstable = 'UNSTABLE'
    radiation_leak = 'RADIATION_LEAK'
    critical_limit = 'CRITICAL_LIMIT'
    civil_unrest = 'CIVIL_UNREST'


class WaypointOrbital(BaseModel):
    """
    An orbital is another waypoint that orbits a parent waypoint.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(
        ..., description='The symbol of the orbiting waypoint.'
    )


class WaypointTraitSymbol(StrEnum):
    """
    The unique identifier of the trait.
    """

    uncharted = 'UNCHARTED'
    under_construction = 'UNDER_CONSTRUCTION'
    marketplace = 'MARKETPLACE'
    shipyard = 'SHIPYARD'
    outpost = 'OUTPOST'
    scattered_settlements = 'SCATTERED_SETTLEMENTS'
    sprawling_cities = 'SPRAWLING_CITIES'
    mega_structures = 'MEGA_STRUCTURES'
    pirate_base = 'PIRATE_BASE'
    overcrowded = 'OVERCROWDED'
    high_tech = 'HIGH_TECH'
    corrupt = 'CORRUPT'
    bureaucratic = 'BUREAUCRATIC'
    trading_hub = 'TRADING_HUB'
    industrial = 'INDUSTRIAL'
    black_market = 'BLACK_MARKET'
    research_facility = 'RESEARCH_FACILITY'
    military_base = 'MILITARY_BASE'
    surveillance_outpost = 'SURVEILLANCE_OUTPOST'
    exploration_outpost = 'EXPLORATION_OUTPOST'
    mineral_deposits = 'MINERAL_DEPOSITS'
    common_metal_deposits = 'COMMON_METAL_DEPOSITS'
    precious_metal_deposits = 'PRECIOUS_METAL_DEPOSITS'
    rare_metal_deposits = 'RARE_METAL_DEPOSITS'
    methane_pools = 'METHANE_POOLS'
    ice_crystals = 'ICE_CRYSTALS'
    explosive_gases = 'EXPLOSIVE_GASES'
    strong_magnetosphere = 'STRONG_MAGNETOSPHERE'
    vibrant_auroras = 'VIBRANT_AURORAS'
    salt_flats = 'SALT_FLATS'
    canyons = 'CANYONS'
    perpetual_daylight = 'PERPETUAL_DAYLIGHT'
    perpetual_overcast = 'PERPETUAL_OVERCAST'
    dry_seabeds = 'DRY_SEABEDS'
    magma_seas = 'MAGMA_SEAS'
    supervolcanoes = 'SUPERVOLCANOES'
    ash_clouds = 'ASH_CLOUDS'
    vast_ruins = 'VAST_RUINS'
    mutated_flora = 'MUTATED_FLORA'
    terraformed = 'TERRAFORMED'
    extreme_temperatures = 'EXTREME_TEMPERATURES'
    extreme_pressure = 'EXTREME_PRESSURE'
    diverse_life = 'DIVERSE_LIFE'
    scarce_life = 'SCARCE_LIFE'
    fossils = 'FOSSILS'
    weak_gravity = 'WEAK_GRAVITY'
    strong_gravity = 'STRONG_GRAVITY'
    crushing_gravity = 'CRUSHING_GRAVITY'
    toxic_atmosphere = 'TOXIC_ATMOSPHERE'
    corrosive_atmosphere = 'CORROSIVE_ATMOSPHERE'
    breathable_atmosphere = 'BREATHABLE_ATMOSPHERE'
    thin_atmosphere = 'THIN_ATMOSPHERE'
    jovian = 'JOVIAN'
    rocky = 'ROCKY'
    volcanic = 'VOLCANIC'
    frozen = 'FROZEN'
    swamp = 'SWAMP'
    barren = 'BARREN'
    temperate = 'TEMPERATE'
    jungle = 'JUNGLE'
    ocean = 'OCEAN'
    radioactive = 'RADIOACTIVE'
    micro_gravity_anomalies = 'MICRO_GRAVITY_ANOMALIES'
    debris_cluster = 'DEBRIS_CLUSTER'
    deep_craters = 'DEEP_CRATERS'
    shallow_craters = 'SHALLOW_CRATERS'
    unstable_composition = 'UNSTABLE_COMPOSITION'
    hollowed_interior = 'HOLLOWED_INTERIOR'
    stripped = 'STRIPPED'


class WaypointType(StrEnum):
    """
    The type of waypoint.
    """

    planet = 'PLANET'
    gas_giant = 'GAS_GIANT'
    moon = 'MOON'
    orbital_station = 'ORBITAL_STATION'
    jump_gate = 'JUMP_GATE'
    asteroid_field = 'ASTEROID_FIELD'
    asteroid = 'ASTEROID'
    engineered_asteroid = 'ENGINEERED_ASTEROID'
    asteroid_base = 'ASTEROID_BASE'
    nebula = 'NEBULA'
    debris_field = 'DEBRIS_FIELD'
    gravity_well = 'GRAVITY_WELL'
    artificial_gravity_well = 'ARTIFICIAL_GRAVITY_WELL'
    fuel_station = 'FUEL_STATION'


class Chart(BaseModel):
    """
    The chart of a system or waypoint, which makes the location visible to other agents.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    waypoint_symbol: constr(min_length=1) | None = Field(
        None, alias='waypointSymbol', description='The symbol of the waypoint.'
    )
    submitted_by: str | None = Field(
        None,
        alias='submittedBy',
        description='The agent that submitted the chart for this waypoint.',
    )
    submitted_on: AwareDatetime | None = Field(
        None,
        alias='submittedOn',
        description='The time the chart for this waypoint was submitted.',
    )


class ConnectedSystem(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the system.')
    sector_symbol: constr(min_length=1) = Field(
        ..., alias='sectorSymbol', description='The sector of this system.'
    )
    type: SystemType
    faction_symbol: str | None = Field(
        None,
        alias='factionSymbol',
        description='The symbol of the faction that owns the connected jump gate in the system.',
    )
    x: int = Field(..., description='Position in the universe in the x axis.')
    y: int = Field(..., description='Position in the universe in the y axis.')
    distance: int = Field(
        ..., description='The distance of this system to the connected Jump Gate.'
    )


class ConstructionMaterial(BaseModel):
    """
    The details of the required construction materials for a given waypoint under construction.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    trade_symbol: TradeSymbol = Field(..., alias='tradeSymbol')
    required: int = Field(..., description='The number of units required.')
    fulfilled: int = Field(
        ..., description='The number of units fulfilled toward the required amount.'
    )


class Contract(BaseModel):
    """
    Contract details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: constr(min_length=1) = Field(..., description='ID of the contract.')
    faction_symbol: constr(min_length=1) = Field(
        ...,
        alias='factionSymbol',
        description='The symbol of the faction that this contract is for.',
    )
    type: Type = Field(..., description='Type of contract.')
    terms: ContractTerms
    accepted: bool = Field(
        ..., description='Whether the contract has been accepted by the agent'
    )
    fulfilled: bool = Field(..., description='Whether the contract has been fulfilled')
    expiration: AwareDatetime = Field(
        ..., deprecated=True, description='Deprecated in favor of deadlineToAccept'
    )
    deadline_to_accept: AwareDatetime | None = Field(
        None,
        alias='deadlineToAccept',
        description='The time at which the contract is no longer available to be accepted',
    )


class ExtractionYield(BaseModel):
    """
    A yield from the extraction operation.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: TradeSymbol
    units: int = Field(
        ...,
        description="The number of units extracted that were placed into the ship's cargo hold.",
    )


class FactionTrait(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: FactionTraitSymbol
    name: str = Field(..., description='The name of the trait.')
    description: str = Field(..., description='A description of the trait.')


class JumpGate(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the waypoint.')
    connections: list[str] = Field(
        ..., description='All the gates that are connected to this waypoint.'
    )


class MarketTradeGood(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: TradeSymbol
    type: Type1 = Field(
        ..., description='The type of trade good (export, import, or exchange).'
    )
    trade_volume: conint(ge=1) = Field(
        ...,
        alias='tradeVolume',
        description='This is the maximum number of units that can be purchased or sold at this market in a single trade for this good. Trade volume also gives an indication of price volatility. A market with a low trade volume will have large price swings, while high trade volume will be more resilient to price changes.',
    )
    supply: SupplyLevel
    activity: ActivityLevel | None = None
    purchase_price: conint(ge=0) = Field(
        ...,
        alias='purchasePrice',
        description='The price at which this good can be purchased from the market.',
    )
    sell_price: conint(ge=0) = Field(
        ...,
        alias='sellPrice',
        description='The price at which this good can be sold to the market.',
    )


class MarketTransaction(BaseModel):
    """
    Result of a transaction with a market.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    waypoint_symbol: constr(min_length=1) = Field(
        ..., alias='waypointSymbol', description='The symbol of the waypoint.'
    )
    ship_symbol: str = Field(
        ...,
        alias='shipSymbol',
        description='The symbol of the ship that made the transaction.',
    )
    trade_symbol: str = Field(
        ..., alias='tradeSymbol', description='The symbol of the trade good.'
    )
    type: Type2 = Field(..., description='The type of transaction.')
    units: conint(ge=0) = Field(
        ..., description='The number of units of the transaction.'
    )
    price_per_unit: conint(ge=0) = Field(
        ..., alias='pricePerUnit', description='The price per unit of the transaction.'
    )
    total_price: conint(ge=0) = Field(
        ..., alias='totalPrice', description='The total price of the transaction.'
    )
    timestamp: AwareDatetime = Field(
        ..., description='The timestamp of the transaction.'
    )


class RepairTransaction(BaseModel):
    """
    Result of a repair transaction.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    waypoint_symbol: constr(min_length=1) = Field(
        ..., alias='waypointSymbol', description='The symbol of the waypoint.'
    )
    ship_symbol: str = Field(
        ..., alias='shipSymbol', description='The symbol of the ship.'
    )
    total_price: conint(ge=0) = Field(
        ..., alias='totalPrice', description='The total price of the transaction.'
    )
    timestamp: AwareDatetime = Field(
        ..., description='The timestamp of the transaction.'
    )


class ScannedSystem(BaseModel):
    """
    Details of a system was that scanned.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='Symbol of the system.')
    sector_symbol: constr(min_length=1) = Field(
        ..., alias='sectorSymbol', description="Symbol of the system's sector."
    )
    type: SystemType
    x: int = Field(..., description='Position in the universe in the x axis.')
    y: int = Field(..., description='Position in the universe in the y axis.')
    distance: int = Field(
        ..., description="The system's distance from the scanning ship."
    )


class ScrapTransaction(BaseModel):
    """
    Result of a scrap transaction.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    waypoint_symbol: constr(min_length=1) = Field(
        ..., alias='waypointSymbol', description='The symbol of the waypoint.'
    )
    ship_symbol: str = Field(
        ..., alias='shipSymbol', description='The symbol of the ship.'
    )
    total_price: conint(ge=0) = Field(
        ..., alias='totalPrice', description='The total price of the transaction.'
    )
    timestamp: AwareDatetime = Field(
        ..., description='The timestamp of the transaction.'
    )


class ShipCargoItem(BaseModel):
    """
    The type of cargo item and the number of units.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: TradeSymbol
    name: str = Field(..., description='The name of the cargo item type.')
    description: str = Field(..., description='The description of the cargo item type.')
    units: conint(ge=1) = Field(
        ..., description='The number of units of the cargo item.'
    )


class ShipEngine(BaseModel):
    """
    The engine determines how quickly a ship travels between waypoints.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: Symbol1 = Field(..., description='The symbol of the engine.')
    name: str = Field(..., description='The name of the engine.')
    description: str = Field(..., description='The description of the engine.')
    condition: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description='The repairable condition of a component. A value of 0 indicates the component needs significant repairs, while a value of 1 indicates the component is in near perfect condition. As the condition of a component is repaired, the overall integrity of the component decreases.',
    )
    integrity: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description='The overall integrity of the component, which determines the performance of the component. A value of 0 indicates that the component is almost completely degraded, while a value of 1 indicates that the component is in near perfect condition. The integrity of the component is non-repairable, and represents permanent wear over time.',
    )
    speed: conint(ge=1) = Field(
        ...,
        description='The speed stat of this engine. The higher the speed, the faster a ship can travel from one point to another. Reduces the time of arrival when navigating the ship.',
    )
    requirements: ShipRequirements
    quality: float = Field(
        ...,
        description='The overall quality of the component, which determines the quality of the component. High quality components return more ships parts and ship plating when a ship is scrapped. But also require more of these parts to repair. This is transparent to the player, as the parts are bought from/sold to the marketplace.',
    )


class ShipFrame(BaseModel):
    """
    The frame of the ship. The frame determines the number of modules and mounting points of the ship, as well as base fuel capacity. As the condition of the frame takes more wear, the ship will become more sluggish and less maneuverable.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: Symbol2 = Field(..., description='Symbol of the frame.')
    name: str = Field(..., description='Name of the frame.')
    description: str = Field(..., description='Description of the frame.')
    condition: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description='The repairable condition of a component. A value of 0 indicates the component needs significant repairs, while a value of 1 indicates the component is in near perfect condition. As the condition of a component is repaired, the overall integrity of the component decreases.',
    )
    integrity: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description='The overall integrity of the component, which determines the performance of the component. A value of 0 indicates that the component is almost completely degraded, while a value of 1 indicates that the component is in near perfect condition. The integrity of the component is non-repairable, and represents permanent wear over time.',
    )
    module_slots: conint(ge=0) = Field(
        ...,
        alias='moduleSlots',
        description='The amount of slots that can be dedicated to modules installed in the ship. Each installed module take up a number of slots, and once there are no more slots, no new modules can be installed.',
    )
    mounting_points: conint(ge=0) = Field(
        ...,
        alias='mountingPoints',
        description='The amount of slots that can be dedicated to mounts installed in the ship. Each installed mount takes up a number of points, and once there are no more points remaining, no new mounts can be installed.',
    )
    fuel_capacity: conint(ge=0) = Field(
        ...,
        alias='fuelCapacity',
        description='The maximum amount of fuel that can be stored in this ship. When refueling, the ship will be refueled to this amount.',
    )
    requirements: ShipRequirements
    quality: float = Field(
        ...,
        description='The overall quality of the component, which determines the quality of the component. High quality components return more ships parts and ship plating when a ship is scrapped. But also require more of these parts to repair. This is transparent to the player, as the parts are bought from/sold to the marketplace.',
    )


class ShipModule(BaseModel):
    """
    A module can be installed in a ship and provides a set of capabilities such as storage space or quarters for crew. Module installations are permanent.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: Symbol3 = Field(..., description='The symbol of the module.')
    capacity: conint(ge=0) | None = Field(
        None,
        description='Modules that provide capacity, such as cargo hold or crew quarters will show this value to denote how much of a bonus the module grants.',
    )
    range: conint(ge=0) | None = Field(
        None,
        description='Modules that have a range will such as a sensor array show this value to denote how far can the module reach with its capabilities.',
    )
    name: str = Field(..., description='Name of this module.')
    description: str = Field(..., description='Description of this module.')
    requirements: ShipRequirements


class ShipMount(BaseModel):
    """
    A mount is installed on the exterier of a ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: Symbol4 = Field(..., description='Symbo of this mount.')
    name: str = Field(..., description='Name of this mount.')
    description: str | None = Field(None, description='Description of this mount.')
    strength: conint(ge=0) | None = Field(
        None,
        description="Mounts that have this value, such as mining lasers, denote how powerful this mount's capabilities are.",
    )
    deposits: list[Deposit] | None = Field(
        None,
        description='Mounts that have this value denote what goods can be produced from using the mount.',
    )
    requirements: ShipRequirements


class ShipNavRouteWaypoint(BaseModel):
    """
    The destination or departure of a ships nav route.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the waypoint.')
    type: WaypointType
    system_symbol: constr(min_length=1) = Field(
        ..., alias='systemSymbol', description='The symbol of the system.'
    )
    x: int = Field(..., description='Position in the universe in the x axis.')
    y: int = Field(..., description='Position in the universe in the y axis.')


class ShipNavRouteWaypointDeprecated(BaseModel):
    """
    Deprecated. Use origin instead.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the waypoint.')
    type: WaypointType
    system_symbol: constr(min_length=1) = Field(
        ..., alias='systemSymbol', description='The symbol of the system.'
    )
    x: int = Field(..., description='Position in the universe in the x axis.')
    y: int = Field(..., description='Position in the universe in the y axis.')


class ShipReactor(BaseModel):
    """
    The reactor of the ship. The reactor is responsible for powering the ship's systems and weapons.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: Symbol5 = Field(..., description='Symbol of the reactor.')
    name: str = Field(..., description='Name of the reactor.')
    description: str = Field(..., description='Description of the reactor.')
    condition: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description='The repairable condition of a component. A value of 0 indicates the component needs significant repairs, while a value of 1 indicates the component is in near perfect condition. As the condition of a component is repaired, the overall integrity of the component decreases.',
    )
    integrity: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description='The overall integrity of the component, which determines the performance of the component. A value of 0 indicates that the component is almost completely degraded, while a value of 1 indicates that the component is in near perfect condition. The integrity of the component is non-repairable, and represents permanent wear over time.',
    )
    power_output: conint(ge=1) = Field(
        ...,
        alias='powerOutput',
        description="The amount of power provided by this reactor. The more power a reactor provides to the ship, the lower the cooldown it gets when using a module or mount that taxes the ship's power.",
    )
    requirements: ShipRequirements
    quality: float = Field(
        ...,
        description='The overall quality of the component, which determines the quality of the component. High quality components return more ships parts and ship plating when a ship is scrapped. But also require more of these parts to repair. This is transparent to the player, as the parts are bought from/sold to the marketplace.',
    )


class ShipRegistration(BaseModel):
    """
    The public registration information of the ship
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    name: constr(min_length=1) = Field(
        ..., description="The agent's registered name of the ship"
    )
    faction_symbol: constr(min_length=1) = Field(
        ...,
        alias='factionSymbol',
        description='The symbol of the faction the ship is registered with',
    )
    role: ShipRole


class ShipyardShip(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: ShipType
    name: str
    description: str
    supply: SupplyLevel
    activity: ActivityLevel | None = None
    purchase_price: int = Field(..., alias='purchasePrice')
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    modules: list[ShipModule]
    mounts: list[ShipMount]
    crew: Crew


class ShipyardTransaction(BaseModel):
    """
    Results of a transaction with a shipyard.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    waypoint_symbol: constr(min_length=1) = Field(
        ..., alias='waypointSymbol', description='The symbol of the waypoint.'
    )
    ship_symbol: str = Field(
        ...,
        alias='shipSymbol',
        deprecated=True,
        description='The symbol of the ship type (e.g. SHIP_MINING_DRONE) that was the subject of the transaction. Contrary to what the name implies, this is NOT the symbol of the ship that was purchased.',
    )
    ship_type: str = Field(
        ...,
        alias='shipType',
        description='The symbol of the ship type (e.g. SHIP_MINING_DRONE) that was the subject of the transaction.',
    )
    price: conint(ge=0) = Field(..., description='The price of the transaction.')
    agent_symbol: str = Field(
        ...,
        alias='agentSymbol',
        description='The symbol of the agent that made the transaction.',
    )
    timestamp: AwareDatetime = Field(
        ..., description='The timestamp of the transaction.'
    )


class SiphonYield(BaseModel):
    """
    A yield from the siphon operation.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: TradeSymbol
    units: int = Field(
        ...,
        description="The number of units siphoned that were placed into the ship's cargo hold.",
    )


class Survey(BaseModel):
    """
    A resource survey of a waypoint, detailing a specific extraction location and the types of resources that can be found there.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    signature: constr(min_length=1) = Field(
        ...,
        description='A unique signature for the location of this survey. This signature is verified when attempting an extraction using this survey.',
    )
    symbol: constr(min_length=1) = Field(
        ..., description='The symbol of the waypoint that this survey is for.'
    )
    deposits: list[SurveyDeposit] = Field(
        ...,
        description='A list of deposits that can be found at this location. A ship will extract one of these deposits when using this survey in an extraction request. If multiple deposits of the same type are present, the chance of extracting that deposit is increased.',
    )
    expiration: AwareDatetime = Field(
        ...,
        description='The date and time when the survey expires. After this date and time, the survey will no longer be available for extraction.',
    )
    size: Size = Field(
        ...,
        description='The size of the deposit. This value indicates how much can be extracted from the survey before it is exhausted.',
    )


class SystemWaypoint(BaseModel):
    """
    Waypoint details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the waypoint.')
    type: WaypointType
    x: int = Field(
        ...,
        description="Relative position of the waypoint on the system's x axis. This is not an absolute position in the universe.",
    )
    y: int = Field(
        ...,
        description="Relative position of the waypoint on the system's y axis. This is not an absolute position in the universe.",
    )
    orbitals: list[WaypointOrbital] = Field(
        ..., description='Waypoints that orbit this waypoint.'
    )
    orbits: constr(min_length=1) | None = Field(
        None,
        description='The symbol of the parent waypoint, if this waypoint is in orbit around another waypoint. Otherwise this value is undefined.',
    )


class TradeGood(BaseModel):
    """
    A good that can be traded for other goods or currency.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: TradeSymbol
    name: str = Field(..., description='The name of the good.')
    description: str = Field(..., description='The description of the good.')


class WaypointModifier(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: WaypointModifierSymbol
    name: str = Field(..., description='The name of the trait.')
    description: str = Field(..., description='A description of the trait.')


class WaypointTrait(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: WaypointTraitSymbol
    name: str = Field(..., description='The name of the trait.')
    description: str = Field(..., description='A description of the trait.')


class Construction(BaseModel):
    """
    The construction details of a waypoint.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The symbol of the waypoint.')
    materials: list[ConstructionMaterial] = Field(
        ..., description='The materials required to construct the waypoint.'
    )
    is_complete: bool = Field(
        ...,
        alias='isComplete',
        description='Whether the waypoint has been constructed.',
    )


class Extraction(BaseModel):
    """
    Extraction details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    ship_symbol: constr(min_length=1) = Field(
        ...,
        alias='shipSymbol',
        description='Symbol of the ship that executed the extraction.',
    )
    yield_: ExtractionYield = Field(..., alias='yield')


class Faction(BaseModel):
    """
    Faction details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: FactionSymbol
    name: constr(min_length=1) = Field(..., description='Name of the faction.')
    description: constr(min_length=1) = Field(
        ..., description='Description of the faction.'
    )
    headquarters: constr(min_length=1) | None = Field(
        None, description="The waypoint in which the faction's HQ is located in."
    )
    traits: list[FactionTrait] = Field(
        ..., description='List of traits that define this faction.'
    )
    is_recruiting: bool = Field(
        ...,
        alias='isRecruiting',
        description='Whether or not the faction is currently recruiting new agents.',
    )


class Market(BaseModel):
    """
    Market details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(
        ...,
        description='The symbol of the market. The symbol is the same as the waypoint where the market is located.',
    )
    exports: list[TradeGood] = Field(
        ..., description='The list of goods that are exported from this market.'
    )
    imports: list[TradeGood] = Field(
        ..., description='The list of goods that are sought as imports in this market.'
    )
    exchange: list[TradeGood] = Field(
        ...,
        description='The list of goods that are bought and sold between agents at this market.',
    )
    transactions: list[MarketTransaction] | None = Field(
        None,
        description='The list of recent transactions at this market. Visible only when a ship is present at the market.',
    )
    trade_goods: list[MarketTradeGood] | None = Field(
        None,
        alias='tradeGoods',
        description='The list of goods that are traded at this market. Visible only when a ship is present at the market.',
    )


class ScannedWaypoint(BaseModel):
    """
    A waypoint that was scanned by a ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the waypoint.')
    type: WaypointType
    system_symbol: constr(min_length=1) = Field(
        ..., alias='systemSymbol', description='The symbol of the system.'
    )
    x: int = Field(..., description='Position in the universe in the x axis.')
    y: int = Field(..., description='Position in the universe in the y axis.')
    orbitals: list[WaypointOrbital] = Field(
        ..., description='List of waypoints that orbit this waypoint.'
    )
    faction: WaypointFaction | None = None
    traits: list[WaypointTrait] = Field(..., description='The traits of the waypoint.')
    chart: Chart | None = None


class ShipCargo(BaseModel):
    """
    Ship cargo details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    capacity: conint(ge=0) = Field(
        ..., description='The max number of items that can be stored in the cargo hold.'
    )
    units: conint(ge=0) = Field(
        ..., description='The number of items currently stored in the cargo hold.'
    )
    inventory: list[ShipCargoItem] = Field(
        ..., description='The items currently in the cargo hold.'
    )


class ShipNavRoute(BaseModel):
    """
    The routing information for the ship's most recent transit or current location.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    destination: ShipNavRouteWaypoint
    origin: ShipNavRouteWaypoint
    departure_time: AwareDatetime = Field(
        ..., alias='departureTime', description="The date time of the ship's departure."
    )
    arrival: AwareDatetime = Field(
        ...,
        description="The date time of the ship's arrival. If the ship is in-transit, this is the expected time of arrival.",
    )


class Shipyard(BaseModel):
    """
    Shipyard details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(
        ...,
        description='The symbol of the shipyard. The symbol is the same as the waypoint where the shipyard is located.',
    )
    ship_types: list[ShipType1] = Field(
        ...,
        alias='shipTypes',
        description='The list of ship types available for purchase at this shipyard.',
    )
    transactions: list[ShipyardTransaction] | None = Field(
        None, description='The list of recent transactions at this shipyard.'
    )
    ships: list[ShipyardShip] | None = Field(
        None,
        description='The ships that are currently available for purchase at the shipyard.',
    )
    modifications_fee: int = Field(
        ...,
        alias='modificationsFee',
        description='The fee to modify a ship at this shipyard. This includes installing or removing modules and mounts on a ship. In the case of mounts, the fee is a flat rate per mount. In the case of modules, the fee is per slot the module occupies.',
    )


class Siphon(BaseModel):
    """
    Siphon details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    ship_symbol: constr(min_length=1) = Field(
        ...,
        alias='shipSymbol',
        description='Symbol of the ship that executed the siphon.',
    )
    yield_: SiphonYield = Field(..., alias='yield')


class System(BaseModel):
    """
    System details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the system.')
    sector_symbol: constr(min_length=1) = Field(
        ..., alias='sectorSymbol', description='The symbol of the sector.'
    )
    constellation: str | None = Field(
        None, description='The constellation that the system is part of.'
    )
    name: str | None = Field(None, description='The name of the system.')
    type: SystemType
    x: int = Field(
        ..., description='Relative position of the system in the sector in the x axis.'
    )
    y: int = Field(
        ..., description='Relative position of the system in the sector in the y axis.'
    )
    waypoints: list[SystemWaypoint] = Field(
        ..., description='Waypoints in this system.'
    )
    factions: list[SystemFaction] = Field(
        ..., description='Factions that control this system.'
    )


class Waypoint(BaseModel):
    """
    A waypoint is a location that ships can travel to such as a Planet, Moon or Space Station.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: constr(min_length=1) = Field(..., description='The symbol of the waypoint.')
    type: WaypointType
    system_symbol: constr(min_length=1) = Field(
        ..., alias='systemSymbol', description='The symbol of the system.'
    )
    x: int = Field(
        ...,
        description="Relative position of the waypoint on the system's x axis. This is not an absolute position in the universe.",
    )
    y: int = Field(
        ...,
        description="Relative position of the waypoint on the system's y axis. This is not an absolute position in the universe.",
    )
    orbitals: list[WaypointOrbital] = Field(
        ..., description='Waypoints that orbit this waypoint.'
    )
    orbits: constr(min_length=1) | None = Field(
        None,
        description='The symbol of the parent waypoint, if this waypoint is in orbit around another waypoint. Otherwise this value is undefined.',
    )
    faction: WaypointFaction | None = None
    traits: list[WaypointTrait] = Field(..., description='The traits of the waypoint.')
    modifiers: list[WaypointModifier] | None = Field(
        None, description='The modifiers of the waypoint.'
    )
    chart: Chart | None = None
    is_under_construction: bool = Field(
        ...,
        alias='isUnderConstruction',
        description='True if the waypoint is under construction.',
    )


class ShipNav(BaseModel):
    """
    The navigation information of the ship.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    system_symbol: constr(min_length=1) = Field(
        ..., alias='systemSymbol', description='The symbol of the system.'
    )
    waypoint_symbol: constr(min_length=1) = Field(
        ..., alias='waypointSymbol', description='The symbol of the waypoint.'
    )
    route: ShipNavRoute
    status: ShipNavStatus
    flight_mode: ShipNavFlightMode = Field(..., alias='flightMode')


class ScannedShip(BaseModel):
    """
    The ship that was scanned. Details include information about the ship that could be detected by the scanner.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(..., description='The globally unique identifier of the ship.')
    registration: ShipRegistration
    nav: ShipNav
    frame: Frame | None = Field(None, description='The frame of the ship.')
    reactor: Reactor | None = Field(None, description='The reactor of the ship.')
    engine: Engine = Field(..., description='The engine of the ship.')
    mounts: list[Mount] | None = Field(
        None, description='List of mounts installed in the ship.'
    )


class Ship(BaseModel):
    """
    Ship details.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )
    symbol: str = Field(
        ...,
        description='The globally unique identifier of the ship in the following format: `[AGENT_SYMBOL]-[HEX_ID]`',
    )
    registration: ShipRegistration
    nav: ShipNav
    crew: ShipCrew
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    cooldown: Cooldown
    modules: list[ShipModule] = Field(
        ..., description='Modules installed in this ship.'
    )
    mounts: list[ShipMount] = Field(..., description='Mounts installed in this ship.')
    cargo: ShipCargo
    fuel: ShipFuel
