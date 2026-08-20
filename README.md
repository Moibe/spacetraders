# SpaceTraders

Cliente Python y bots para [SpaceTraders.io](https://spacetraders.io), el juego que se
juega enteramente por API: manejas un agente que comercia, mina, explora y expande una
flota en un universo compartido.

Probado contra la API **v2.3.0**.

## Qué hay acá

```
spacetraders/          el cliente
  client.py            nucleo HTTP: rate limit, reintentos, paginacion
  session.py           identidad del agente, token persistido, resets del servidor
  config.py            configuracion desde .env
  errors.py            jerarquia de excepciones
  ratelimit.py         token bucket (2 req/s, rafaga de 30)
  models.py            96 modelos pydantic GENERADOS del OpenAPI oficial
  api/                 un modulo por area: fleet, contracts, systems, factions, agents
  cli.py               `python -m spacetraders <comando>`
bots/
  contract_runner.py   bot que cierra contratos de aprovisionamiento
tools/
  generate_models.py   regenera models.py desde el spec oficial
tests/                 49 tests (45 sin red + 4 contra la API real)
```

## Arranque

### 1. Instalar

```bash
python -m venv venv
venv\Scripts\activate            # Windows;  source venv/bin/activate en Linux/macOS
pip install -r requirements-dev.txt
```

### 2. Conseguir el token de cuenta

Este es el único paso manual y no se puede automatizar: creá una cuenta en
**https://my.spacetraders.io** y copiá tu **account token**.

Es importante no confundir los dos tokens que maneja el juego:

| Token | De dónde sale | Para qué sirve |
|---|---|---|
| **Account token** | dashboard | firma **solo** `POST /register` |
| **Agent token** | lo devuelve el registro | firma los otros 54 endpoints |

### 3. Configurar

```bash
cp .env.example .env      # copy .env.example .env en Windows
```

Y en `.env`: pegá el account token y elegí el nombre de tu agente (3–14 caracteres).

### 4. Registrar y jugar

```bash
python -m spacetraders status       # estado del servidor (no necesita token)
python -m spacetraders register     # crea el agente y guarda su token
python -m spacetraders whoami       # quien sos y cuanto tenes
python -m spacetraders ships        # tu flota
python -m spacetraders contracts    # tus contratos
```

El registro te da nave de comando, sonda, un contrato inicial y **175.000 créditos**.

## El reset semanal

El universo se resetea **todos los sábados**: se borra el progreso y **se invalidan
todos los tokens de agente**. Por eso el cliente nunca guarda un token solo, sino el par
`(token, resetDate)`:

```
.spacetraders/agent.json
{
  "agent_symbol": "MOIBE_1",
  "faction": "COSMIC",
  "token": "...",
  "reset_date": "2026-08-16",
  "created_at": "2026-08-19T20:00:00+00:00"
}
```

Al arrancar, `Session.ensure_agent()` compara ese `reset_date` contra el `resetDate` que
publica `GET /` y, si cambió, **re-registra el agente solo** con el account token. El
sábado no hay que tocar nada.

Si preferís que falle en vez de re-registrar, poné `SPACETRADERS_AUTO_REREGISTER=0` y
vas a recibir un `ServerResetError`.

Fecha del próximo reset, en cualquier momento: `python -m spacetraders status`.

## Usarlo como librería

```python
from spacetraders import Session

with Session.from_env() as sesion:
    agente = sesion.ensure_agent()          # registra o reusa el token guardado
    print(agente.symbol, agente.credits)

    nave = sesion.fleet.list_ships()[0]
    sistema = nave.nav.system_symbol

    # Filtrar del lado del servidor: las peticiones son el recurso escaso
    for wp in sesion.systems.find_marketplaces(sistema):
        mercado = sesion.systems.get_market(wp.symbol)
        print(wp.symbol, [str(b.symbol) for b in mercado.exports])

    # Comerciar
    sesion.fleet.orbit(nave.symbol)
    sesion.fleet.navigate(nave.symbol, "X1-AA11-B2")
    sesion.fleet.dock(nave.symbol)
    sesion.fleet.refuel(nave.symbol)
    venta = sesion.fleet.sell_cargo(nave.symbol, "IRON_ORE", 10)
    print(venta.transaction.total_price, venta.agent.credits)
```

Todo devuelve modelos pydantic tipados. Los campos son `snake_case` en Python y viajan
como `camelCase` a la API.

### El cliente HTTP se encarga de

- **Rate limit**: token bucket de 2 req/s con ráfaga de 30, los números que publica la
  propia API en sus cabeceras `X-RateLimit-*`.
- **429**: espera lo que dice `Retry-After` y además deja el bucket seco antes de
  reintentar.
- **5xx y cortes de red**: reintento con backoff exponencial y jitter. Los `POST`
  **no** se reintentan ante un fallo sin respuesta, para no comprar o entregar dos veces.
- **Paginación**: `paginate()` recorre páginas hasta `meta.total`, con `max_pages` para
  no barrer los 200.000 waypoints del universo sin querer.
- **Errores**: `UnauthorizedError`, `NotFoundError`, `RateLimitError`, `ServerError`,
  todos con el `code` y el `requestId` de la API.

## El bot de contratos

```bash
python -m bots.contract_runner --cycles 1
python -m bots.contract_runner --ship MOIBE_1-1 --cycles 3 -v
```

Cierra el primer loop rentable del juego con una sola nave: acepta (o negocia) un
contrato de aprovisionamiento, busca la mercancía en los mercados del sistema, compra en
tandas del tamaño del `trade_volume`, vuela al destino, entrega y cumple.

Es a propósito conservador: una nave, un solo sistema, y deja siempre 5.000 créditos de
reserva. Si el destino del contrato está en otro sistema, avisa y se detiene en vez de
improvisar (le falta `warp`/`jump` para eso).

## Regenerar los modelos

`spacetraders/models.py` es **generado** — no editarlo a mano. Cuando la API cambie de
versión:

```bash
python tools/generate_models.py
```

Clona el spec oficial, junta los 76 JSON Schema sueltos en un OpenAPI autocontenido y
corre `datamodel-code-generator`. La cabecera del archivo no lleva timestamp, así que el
diff muestra sólo los cambios reales del spec.

## Tests

```bash
pytest                      # todo
pytest -m "not network"     # solo los offline (sin internet)
pytest -m network           # solo los de contrato contra la API real
ruff check .                # lint
```

Los tests de red sólo usan endpoints públicos: no tocan tu agente ni gastan créditos.
Uno de ellos verifica que las cabeceras de rate limit sigan diciendo 2/s y ráfaga 30 —
si el juego los cambia, ese test avisa antes de que te empiecen a llover 429.

## Qué falta

- `warp`/`jump` en el bot para contratos entre sistemas
- estrategia de minería (el cliente ya tiene `survey`/`extract`/`siphon`)
- arbitraje de mercados usando `/market/supply-chain`
- comprar y coordinar más de una nave
