# Cómo funciona SpaceTraders

Notas del juego, con datos reales medidos en la temporada del **2026-08-16** desde el
agente `MOIBE` (sistema `X1-SC86`). Los números concretos van a cambiar en cada reset,
pero las mecánicas no.

## Qué es

Un MMO económico **sin interfaz**. No hay cliente que abrir: la API *es* el juego. Todos
los jugadores comparten un universo y compiten por dinero. Como cada acción es una
petición HTTP, el juego real no es táctico sino de programación — el rival es tu propia
arquitectura.

Referencia: el puntero del leaderboard andaba por **1,200 millones** de créditos mientras
nosotros teníamos 181,913. Esa diferencia no es habilidad manual, es automatización.

## Estados y sustantivos

```
universo
 └─ sistema            (7,006 en total)
     └─ waypoint       (200,160 en total; planetas, lunas, asteroides, estaciones)
         ├─ MARKETPLACE   compra/venta de mercancías
         ├─ SHIPYARD      compra de naves, módulos y mounts
         ├─ JUMP_GATE     salto instantáneo a otros sistemas
         └─ depósitos     lo que se puede minar ahí
```

Un waypoint puede ser varias cosas a la vez (planeta + mercado + astillero). Lo que
define su utilidad son sus **rasgos** (`traits`), no su tipo.

Los símbolos codifican la jerarquía: `X1-SC86-B7` = sector `X1`, sistema `X1-SC86`,
waypoint `B7`. De ahí sale el helper `spacetraders.api.system_of()`.

### Ejemplo real: X1-SC86 (estrella roja, 91 waypoints)

| Tipo | Cantidad |
|---|---|
| ASTEROID | 57 |
| MOON | 15 |
| PLANET | 7 |
| FUEL_STATION | 4 |
| ORBITAL_STATION | 3 |
| ASTEROID_BASE | 2 |
| ENGINEERED_ASTEROID | 1 |
| GAS_GIANT | 1 |
| JUMP_GATE | 1 |

De esos 91 waypoints, **28 tienen mercado** y 3 tienen astillero.

## Las restricciones (acá está el juego)

- **Tiempo real.** Un tramo entre dos waypoints del mismo sistema tardó ~4 minutos. No
  hay forma de acelerar.
- **Combustible.** Ese tramo consumió 318 de 400. **Solo se puede recargar donde ya
  estás**, así que salir con el tanque corto no es recuperable: hay que llenar antes de
  despegar.
- **Modos de vuelo.** `DRIFT` gasta 1 de combustible pero tarda muchísimo (el salvavidas
  cuando quedaste corto), `CRUISE` es el normal, `BURN` es rápido y caro, `STEALTH` evita
  escaneos.
- **Bodega.** La nave de comando lleva 40 unidades. Un contrato de 59 son dos viajes.
- **Cooldowns.** Minar, escanear y saltar dejan la nave inutilizable un rato.
- **2 peticiones por segundo** (ráfaga de 30). El recurso más escaso del juego no son los
  créditos, son las peticiones — de ahí que convenga filtrar del lado del servidor.
- **Reset semanal**, los sábados. Se borra todo el progreso y se invalidan los tokens.

## La economía

Cada mercado **importa** unas mercancías y **exporta** otras:

- quien **importa** algo, lo paga bien;
- quien **exporta** algo, lo vende barato;
- lo que figura como **exchange** se compra y vende a precio de mercado.

Comprar donde se exporta y vender donde se importa *es* el negocio.

Hay cadenas de producción reales (129 mercancías mapeadas en
`GET /market/supply-chain`):

```
IRON          <- IRON_ORE
IRON_ORE      <- EXPLOSIVES
FUEL          <- HYDROCARBON
ELECTRONICS   <- SILICON_CRYSTALS + COPPER
SHIP_PLATING  <- ALUMINUM + MACHINERY
```

### Un circuito cerrado real dentro de X1-SC86

```
B7    intercambia IRON_ORE (56 cr)      materia prima barata
H60   importa IRON_ORE  → exporta IRON  le vendes mineral, le compras metal
K91   importa IRON_ORE  → exporta IRON
F54   importa IRON      → exporta EXPLOSIVES
```

El contrato inicial pedía entregar IRON_ORE en K91, que justamente lo importa: los
contratos siguen la lógica de la economía, no son aleatorios.

**Detalle medido:** el `trade_volume` de IRON_ORE en B7 es 180. Compramos 40 y después
19, las dos tandas a 56 exactos — demasiado chicas para mover el precio. Comprar por
encima del `trade_volume` sí lo empuja en contra.

**Los precios solo se ven teniendo una nave en el waypoint.** Sin nave presente solo
aparecen las listas de imports/exports/exchange. Por eso las sondas valen: se dejan
estacionadas en un mercado y reportan precios sin costo de viaje.

## Las tres formas de ganar dinero

1. **Contratos.** Predecibles y el juego te dice qué hacer. Medido: **+6,913 créditos en
   17 minutos** con una sola nave. Tipos: `PROCUREMENT` (entregar mercancía), `TRANSPORT`
   y `SHUTTLE`. Ciclo: aceptar (cobras anticipo) → entregar → cumplir (cobras el resto),
   siempre antes del `deadline`.
2. **Arbitraje.** Comprar y vender sobre el circuito de arriba. Escala mucho mejor que los
   contratos, pero exige descubrir precios primero.
3. **Minería.** 57 asteroides en el sistema. Necesita mounts de láser minero; un `survey`
   mapea los depósitos y mejora el rendimiento. El gigante gaseoso se sifonea con
   `siphon`.

## Progresión

**Más naves.** Los astilleros de X1-SC86 y su stock:

```
X1-SC86-A2   SHIP_PROBE, SHIP_LIGHT_SHUTTLE, SHIP_LIGHT_HAULER
X1-SC86-C44  SHIP_PROBE, SHIP_SIPHON_DRONE
X1-SC86-H61  SHIP_MINING_DRONE, SHIP_SURVEYOR
```

Un `LIGHT_HAULER` es más bodega (menos viajes por contrato); `MINING_DRONE` +
`SURVEYOR` abren la minería; los `PROBE` son ojos baratos en mercados.

**Salir del sistema.** El jump gate `X1-SC86-I64` conecta con `X1-CF23`, `X1-NH23` y
`X1-AU12`. Saltar es instantáneo, cuesta créditos y deja cooldown. `warp` viaja sin
puerta pero es carísimo en combustible.

**Mejorar naves.** Módulos (bodega, refinería) y mounts (láseres, sensores) se instalan
en astilleros — vimos un `MOUNT_MINING_LASER_II` en venta en `X1-SC86-G58`.

## Nada pasa solo

Importante para no confundirse: el juego es **asíncrono pero no pasivo**. Si no hay un
proceso corriendo, tus naves están estacionadas y tus créditos quietos. No hay renta ni
producción de fondo. Lo único que corre solo es el reloj del reset.

Es decir: "estar jugando" = tener un bot corriendo.
