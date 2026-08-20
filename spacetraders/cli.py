"""CLI del cliente: `python -m spacetraders <comando>`.

Sirve para lo que no vale la pena scriptear: ver el estado del servidor, registrar
el agente, mirar la flota, los contratos o un mercado.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from .api import system_of
from .client import ApiClient
from .errors import SpaceTradersError
from .session import Session


def _log_setup(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)-7s %(name)s: %(message)s",
    )
    if not verbose:
        # A nivel INFO el cliente HTTP solo deberia hablar cuando algo se reintenta.
        logging.getLogger("spacetraders.client").setLevel(logging.WARNING)


# --------------------------------------------------------------------- comandos


def cmd_status(_args: argparse.Namespace) -> int:
    """Estado del servidor: no necesita token."""
    estado = ApiClient().get_status()
    print(estado["status"])
    print(f"  version    : {estado['version']}")
    print(f"  temporada  : arranco {estado['resetDate']}")
    resets = estado["serverResets"]
    print(f"  proximo reset: {resets['next']} ({resets['frequency']})")
    stats = estado.get("stats", {})
    print(
        "  universo   : "
        f"{stats.get('agents')} agentes, {stats.get('ships')} naves, "
        f"{stats.get('systems')} sistemas, {stats.get('waypoints')} waypoints"
    )
    lider = (estado.get("leaderboards", {}).get("mostCredits") or [{}])[0]
    if lider:
        creditos = lider.get("credits") or 0
        print(f"  puntero    : {lider.get('agentSymbol')} con {creditos:,} creditos")
    for anuncio in estado.get("announcements", [])[:2]:
        print(f"  aviso      : {anuncio.get('title')}")
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    """Registra el agente (o lo re-registra si ya hay uno de esta temporada)."""
    with Session.from_env() as sesion:
        registro = sesion.register(symbol=args.symbol, faction=args.faction)
        agente = registro.agent
        print(f"Agente {agente.symbol} registrado en {agente.starting_faction}")
        print(f"  creditos : {agente.credits:,}")
        print(f"  base     : {agente.headquarters}")
        print(f"  naves    : {', '.join(n.symbol for n in registro.ships)}")
        print(f"  contrato : {registro.contract.id} ({registro.contract.type})")
        print(f"  token    : guardado en {sesion.store.path}")
    return 0


def cmd_whoami(_args: argparse.Namespace) -> int:
    """Quien soy en esta temporada, resolviendo el token como lo hace el bot."""
    with Session.from_env() as sesion:
        agente = sesion.ensure_agent()
        print(f"{agente.symbol} ({agente.starting_faction})")
        print(f"  creditos : {agente.credits:,}")
        print(f"  base     : {agente.headquarters}")
        print(f"  naves    : {agente.ship_count}")
        print(f"  temporada: {sesion.reset_date}")
    return 0


def cmd_ships(_args: argparse.Namespace) -> int:
    """Flota con su estado de navegacion, combustible y bodega."""
    with Session.from_env() as sesion:
        sesion.ensure_agent()
        naves = sesion.fleet.list_ships()
        if not naves:
            print("Sin naves.")
            return 0
        for nave in naves:
            carga = f"{nave.cargo.units}/{nave.cargo.capacity}"
            combustible = f"{nave.fuel.current}/{nave.fuel.capacity}"
            print(
                f"{nave.symbol:<20} {nave.registration.role:<12} "
                f"{nave.nav.status:<12} {nave.nav.waypoint_symbol:<18} "
                f"fuel {combustible:<10} carga {carga}"
            )
            for item in nave.cargo.inventory:
                print(f"    {item.units:>4} x {item.symbol}")
    return 0


def cmd_contracts(_args: argparse.Namespace) -> int:
    """Contratos con su estado, pago y mercancia pendiente."""
    with Session.from_env() as sesion:
        sesion.ensure_agent()
        contratos = sesion.contracts.list_contracts()
        if not contratos:
            print("Sin contratos. Podes negociar uno con: negotiate <NAVE>")
            return 0
        for c in contratos:
            estado = "cumplido" if c.fulfilled else ("aceptado" if c.accepted else "ofrecido")
            pago = c.terms.payment
            print(
                f"{c.id}  {c.type:<12} {estado:<9} "
                f"pago {pago.on_accepted:,} + {pago.on_fulfilled:,}  "
                f"vence {c.terms.deadline:%Y-%m-%d %H:%M}"
            )
            for entrega in c.terms.deliver or []:
                print(
                    f"    {entrega.units_fulfilled}/{entrega.units_required} "
                    f"{entrega.trade_symbol} -> {entrega.destination_symbol}"
                )
    return 0


def cmd_negotiate(args: argparse.Namespace) -> int:
    """Pide un contrato nuevo con una nave atracada."""
    with Session.from_env() as sesion:
        sesion.ensure_agent()
        contrato = sesion.contracts.negotiate(args.ship)
        print(f"Contrato nuevo: {contrato.id} ({contrato.type})")
        for entrega in contrato.terms.deliver or []:
            print(
                f"    {entrega.units_required} {entrega.trade_symbol} "
                f"-> {entrega.destination_symbol}"
            )
    return 0


def cmd_waypoints(args: argparse.Namespace) -> int:
    """Waypoints de un sistema, con filtros del lado del servidor."""
    with Session.from_env() as sesion:
        agente = sesion.ensure_agent()
        sistema = args.system or system_of(agente.headquarters)
        waypoints = sesion.systems.list_waypoints(
            sistema, traits=args.trait, waypoint_type=args.type
        )
        print(f"{len(waypoints)} waypoints en {sistema}")
        for w in waypoints:
            rasgos = ", ".join(t.symbol for t in w.traits or [])
            print(f"  {w.symbol:<18} {w.type:<22} {rasgos}")
    return 0


def cmd_market(args: argparse.Namespace) -> int:
    """Mercado de un waypoint (con precios si tenes una nave ahi)."""
    with Session.from_env() as sesion:
        sesion.ensure_agent()
        mercado = sesion.systems.get_market(args.waypoint)
        print(f"Mercado en {mercado.symbol}")
        if mercado.trade_goods:
            print(f"  {'mercancia':<28} {'compra':>8} {'venta':>8} {'volumen':>8}  suministro")
            for g in mercado.trade_goods:
                print(
                    f"  {g.symbol:<28} {g.purchase_price:>8,} {g.sell_price:>8,} "
                    f"{g.trade_volume:>8}  {g.supply}"
                )
        else:
            print("  (sin precios: hace falta una nave en el waypoint)")
            for etiqueta, bienes in (
                ("importa", mercado.imports),
                ("exporta", mercado.exports),
                ("intercambia", mercado.exchange),
            ):
                if bienes:
                    print(f"  {etiqueta}: {', '.join(b.symbol for b in bienes)}")
    return 0


def cmd_shipyard(args: argparse.Namespace) -> int:
    """Naves en venta en un astillero."""
    with Session.from_env() as sesion:
        sesion.ensure_agent()
        astillero = sesion.systems.get_shipyard(args.waypoint)
        print(f"Astillero en {astillero.symbol}")
        if astillero.ships:
            for nave in astillero.ships:
                print(f"  {nave.type:<22} {nave.purchase_price:>10,} creditos")
        else:
            print("  tipos disponibles (sin precios, hace falta una nave presente):")
            for tipo in astillero.ship_types:
                print(f"    {tipo.type}")
    return 0


# ----------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m spacetraders",
        description="Cliente de SpaceTraders: estado, registro y consultas rapidas.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="logs de debug")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("status", help="estado del servidor (sin token)").set_defaults(
        func=cmd_status
    )

    p_reg = sub.add_parser("register", help="registra el agente con el token de cuenta")
    p_reg.add_argument("--symbol", help="simbolo del agente (3-14 caracteres)")
    p_reg.add_argument("--faction", help="faccion inicial (default COSMIC)")
    p_reg.set_defaults(func=cmd_register)

    sub.add_parser("whoami", help="datos del agente activo").set_defaults(func=cmd_whoami)
    sub.add_parser("ships", help="lista la flota").set_defaults(func=cmd_ships)
    sub.add_parser("contracts", help="lista los contratos").set_defaults(func=cmd_contracts)

    p_neg = sub.add_parser("negotiate", help="pide un contrato nuevo")
    p_neg.add_argument("ship", help="simbolo de la nave (atracada)")
    p_neg.set_defaults(func=cmd_negotiate)

    p_way = sub.add_parser("waypoints", help="waypoints de un sistema")
    p_way.add_argument("system", nargs="?", help="default: el sistema de tu base")
    p_way.add_argument("--trait", help="filtra por rasgo (ej. MARKETPLACE, SHIPYARD)")
    p_way.add_argument("--type", help="filtra por tipo (ej. ASTEROID, PLANET)")
    p_way.set_defaults(func=cmd_waypoints)

    p_mkt = sub.add_parser("market", help="precios de un mercado")
    p_mkt.add_argument("waypoint", help="simbolo del waypoint")
    p_mkt.set_defaults(func=cmd_market)

    p_sy = sub.add_parser("shipyard", help="naves en venta en un astillero")
    p_sy.add_argument("waypoint", help="simbolo del waypoint")
    p_sy.set_defaults(func=cmd_shipyard)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _log_setup(args.verbose)
    try:
        resultado: Any = args.func(args)
        return int(resultado or 0)
    except SpaceTradersError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ncancelado", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
