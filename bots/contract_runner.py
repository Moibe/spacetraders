"""Bot de contratos de aprovisionamiento (PROCUREMENT).

Cierra el primer loop rentable del juego con una sola nave:

    aceptar contrato -> comprar la mercancia en un mercado del sistema
    -> volar al destino -> entregar -> cumplir y cobrar

Es deliberadamente conservador: una nave, un sistema, compras limitadas por el
`trade_volume` del mercado y por los creditos disponibles. La idea es que sea
legible y que no te funda la cuenta, no que gane el leaderboard.

Uso:

    python -m bots.contract_runner --cycles 1
"""

from __future__ import annotations

import argparse
import logging

from spacetraders import ApiError, Session, SpaceTradersError
from spacetraders.api import system_of
from spacetraders.models import Contract, Market, Ship, ShipNavFlightMode

log = logging.getLogger("bots.contract_runner")

# Margen para no quedar sin creditos por completo tras una compra.
RESERVA_DE_CREDITOS = 5_000
# Antes de cada salida se llena el tanque si esta por debajo de esto. Alto a
# proposito: solo se puede recargar donde ya estas, asi que salir corto es la
# forma mas facil de quedar varado.
UMBRAL_DE_COMBUSTIBLE = 0.9

# Codigo de la API cuando el tramo pide mas combustible del que hay a bordo.
CODE_COMBUSTIBLE_INSUFICIENTE = 4203


class ContractRunner:
    """Ejecuta contratos de aprovisionamiento con una nave."""

    def __init__(self, session: Session, ship_symbol: str | None = None) -> None:
        self.sesion = session
        self.fleet = session.fleet
        self.contracts = session.contracts
        self.systems = session.systems
        self._ship_symbol = ship_symbol

    # ------------------------------------------------------------------ arranque

    def elegir_nave(self) -> Ship:
        """Elige la nave de carga mas grande (la de comando al principio)."""
        if self._ship_symbol:
            return self.fleet.get_ship(self._ship_symbol)

        naves = self.fleet.list_ships()
        if not naves:
            raise SpaceTradersError("El agente no tiene naves.")
        carguera = max(naves, key=lambda n: n.cargo.capacity)
        if carguera.cargo.capacity == 0:
            raise SpaceTradersError(
                "Ninguna nave tiene bodega; un contrato de aprovisionamiento necesita carga."
            )
        log.info(
            "nave elegida: %s (bodega %s, rol %s)",
            carguera.symbol,
            carguera.cargo.capacity,
            carguera.registration.role,
        )
        return carguera

    def elegir_contrato(self, ship: Ship) -> Contract | None:
        """Devuelve un contrato de aprovisionamiento listo para trabajar.

        Prioriza uno ya aceptado; si no hay, acepta uno ofrecido; y si tampoco,
        negocia uno nuevo con la nave atracada.
        """
        pendientes = [c for c in self.contracts.pending() if self._es_aprovisionamiento(c)]
        if pendientes:
            contrato = pendientes[0]
            log.info("retomando contrato aceptado %s", contrato.id)
            return contrato

        ofrecidos = [c for c in self.contracts.available() if self._es_aprovisionamiento(c)]
        if not ofrecidos:
            log.info("no hay contratos ofrecidos; negociando uno nuevo")
            self._atracar(ship)
            nuevo = self.contracts.negotiate(ship.symbol)
            ofrecidos = [nuevo] if self._es_aprovisionamiento(nuevo) else []
            if not ofrecidos:
                log.warning("el contrato negociado no es de aprovisionamiento; se deja pasar")
                return None

        contrato = ofrecidos[0]
        pago = contrato.terms.payment
        log.info(
            "aceptando contrato %s: %s + %s creditos, vence %s",
            contrato.id,
            f"{pago.on_accepted:,}",
            f"{pago.on_fulfilled:,}",
            contrato.terms.deadline,
        )
        acuerdo = self.contracts.accept(contrato.id)
        log.info("anticipo cobrado, saldo %s creditos", f"{acuerdo.agent.credits:,}")
        return acuerdo.contract

    @staticmethod
    def _es_aprovisionamiento(contrato: Contract) -> bool:
        return bool(contrato.terms.deliver) and str(contrato.type) == "PROCUREMENT"

    # -------------------------------------------------------------------- ciclo

    def run(self, cycles: int = 1) -> None:
        """Trabaja hasta `cycles` contratos, uno despues del otro."""
        agente = self.sesion.ensure_agent()
        log.info("agente %s con %s creditos", agente.symbol, f"{agente.credits:,}")

        nave = self.elegir_nave()
        for ciclo in range(1, cycles + 1):
            log.info("--- ciclo %s/%s ---", ciclo, cycles)
            contrato = self.elegir_contrato(nave)
            if contrato is None:
                log.info("sin contrato utilizable; corto aca")
                return
            self.trabajar_contrato(contrato, nave)
            nave = self.fleet.get_ship(nave.symbol)

    def trabajar_contrato(self, contrato: Contract, nave: Ship) -> None:
        """Compra y entrega todo lo que pide el contrato, y lo cumple al terminar."""
        for entrega in contrato.terms.deliver or []:
            mercancia = str(entrega.trade_symbol)
            destino = entrega.destination_symbol
            faltante = entrega.units_required - entrega.units_fulfilled
            if faltante <= 0:
                continue

            log.info("pendiente: %s x %s -> %s", faltante, mercancia, destino)
            if system_of(destino) != nave.nav.system_symbol:
                log.error(
                    "el destino %s esta en otro sistema (%s); este bot solo opera "
                    "dentro del sistema actual (%s). Mover la nave a mano, o extender "
                    "el bot con warp/jump.",
                    destino,
                    system_of(destino),
                    nave.nav.system_symbol,
                )
                return

            while faltante > 0:
                comprado = self.comprar(nave, mercancia, faltante)
                if comprado == 0:
                    log.error("no se pudo comprar %s; se abandona esta entrega", mercancia)
                    return
                entregado = self.entregar(contrato, nave, mercancia, destino)
                faltante -= entregado
                if entregado == 0:
                    log.error("la entrega no avanzo; se corta para no ciclar en falso")
                    return
                nave = self.fleet.get_ship(nave.symbol)

        contrato = self.contracts.get_contract(contrato.id)
        if self._todo_entregado(contrato):
            acuerdo = self.contracts.fulfill(contrato.id)
            log.info(
                "contrato %s cumplido; saldo %s creditos",
                contrato.id,
                f"{acuerdo.agent.credits:,}",
            )

    @staticmethod
    def _todo_entregado(contrato: Contract) -> bool:
        return all(
            d.units_fulfilled >= d.units_required for d in (contrato.terms.deliver or [])
        )

    # ------------------------------------------------------------------ compras

    def comprar(self, nave: Ship, mercancia: str, tope: int) -> int:
        """Compra hasta `tope` unidades (o lo que quepa/alcance) y devuelve cuantas.

        Busca el mercado en el sistema que venda la mercancia, vuela, atraca y
        compra en tandas del tamano del `trade_volume` para no mover el precio de
        golpe ni pasarse del volumen permitido.
        """
        ya_a_bordo = self._unidades_a_bordo(nave, mercancia)
        if ya_a_bordo >= tope:
            log.info("ya hay %s x %s a bordo; no hace falta comprar", ya_a_bordo, mercancia)
            return ya_a_bordo

        mercado_wp = self.buscar_mercado(nave.nav.system_symbol, mercancia)
        if mercado_wp is None:
            log.error("ningun mercado de %s vende %s", nave.nav.system_symbol, mercancia)
            return ya_a_bordo

        self.viajar(nave, mercado_wp)
        self._atracar(nave)

        mercado = self.systems.get_market(mercado_wp)
        precio, volumen = self._precio_y_volumen(mercado, mercancia)
        if precio is None:
            log.error("el mercado %s no publica precio para %s", mercado_wp, mercancia)
            return ya_a_bordo

        agente = self.sesion.get_my_agent()
        nave = self.fleet.get_ship(nave.symbol)
        espacio = nave.cargo.capacity - nave.cargo.units
        asequible = max(0, (agente.credits - RESERVA_DE_CREDITOS) // precio)
        objetivo = min(tope - ya_a_bordo, espacio, asequible)

        if objetivo <= 0:
            log.error(
                "no se puede comprar %s: espacio=%s, asequible=%s (precio %s, saldo %s)",
                mercancia,
                espacio,
                asequible,
                precio,
                f"{agente.credits:,}",
            )
            return ya_a_bordo

        comprado = 0
        while comprado < objetivo:
            tanda = min(volumen, objetivo - comprado)
            operacion = self.fleet.purchase_cargo(nave.symbol, mercancia, tanda)
            comprado += tanda
            log.info(
                "compradas %s x %s por %s creditos (saldo %s)",
                tanda,
                mercancia,
                f"{operacion.transaction.total_price:,}",
                f"{operacion.agent.credits:,}",
            )

        return ya_a_bordo + comprado

    def buscar_mercado(self, system_symbol: str, mercancia: str) -> str | None:
        """Waypoint del sistema cuyo mercado vende la mercancia.

        Se usa la lista de `exports`/`exchange`, que es visible sin tener una nave
        presente; los precios recien aparecen al llegar.
        """
        for waypoint in self.systems.find_marketplaces(system_symbol):
            try:
                mercado = self.systems.get_market(waypoint.symbol)
            except ApiError as exc:
                log.warning("no se pudo leer el mercado de %s: %s", waypoint.symbol, exc)
                continue
            vendidos = {
                str(b.symbol)
                for grupo in (mercado.exports, mercado.exchange, mercado.trade_goods)
                for b in (grupo or [])
            }
            if mercancia in vendidos:
                log.info("%s se consigue en %s", mercancia, waypoint.symbol)
                return waypoint.symbol
        return None

    @staticmethod
    def _precio_y_volumen(mercado: Market, mercancia: str) -> tuple[int | None, int]:
        for bien in mercado.trade_goods or []:
            if str(bien.symbol) == mercancia:
                return bien.purchase_price, max(1, bien.trade_volume)
        return None, 1

    @staticmethod
    def _unidades_a_bordo(nave: Ship, mercancia: str) -> int:
        return sum(i.units for i in nave.cargo.inventory if str(i.symbol) == mercancia)

    # ----------------------------------------------------------------- entregas

    def entregar(self, contrato: Contract, nave: Ship, mercancia: str, destino: str) -> int:
        """Lleva la carga al destino y la entrega. Devuelve las unidades entregadas."""
        nave = self.fleet.get_ship(nave.symbol)
        unidades = self._unidades_a_bordo(nave, mercancia)
        if unidades == 0:
            return 0

        self.viajar(nave, destino)
        self._atracar(nave)
        entrega = self.contracts.deliver(contrato.id, nave.symbol, mercancia, unidades)
        avance = next(
            (
                d
                for d in entrega.contract.terms.deliver or []
                if str(d.trade_symbol) == mercancia
            ),
            None,
        )
        if avance is not None:
            log.info(
                "entregadas %s x %s (%s/%s)",
                unidades,
                mercancia,
                avance.units_fulfilled,
                avance.units_required,
            )
        return unidades

    # ---------------------------------------------------------------- movimiento

    def viajar(self, nave: Ship, destino: str) -> None:
        """Lleva la nave al waypoint, esperando la llegada si hace falta.

        Antes de salir llena el tanque, porque el unico lugar donde se puede
        recargar es el waypoint donde ya estas: si sales corto, quedas varado sin
        combustible ni forma de comprarlo. Y si aun asi no alcanza, se cae a modo
        DRIFT, que consume 1 de combustible a cambio de tardar muchisimo mas.
        """
        nav = self.fleet.wait_for_arrival(nave.symbol)
        if nav.waypoint_symbol == destino:
            return

        self.recargar(nave)
        self._orbitar(nave)

        try:
            resultado = self.fleet.navigate(nave.symbol, destino)
        except ApiError as exc:
            if exc.code != CODE_COMBUSTIBLE_INSUFICIENTE:
                raise
            log.warning("%s", exc.message)
            resultado = self._navegar_a_la_deriva(nave, destino)

        log.info(
            "navegando a %s, llega %s (fuel %s/%s)",
            destino,
            resultado.nav.route.arrival,
            resultado.fuel.current if resultado.fuel else "?",
            resultado.fuel.capacity if resultado.fuel else "?",
        )
        self.fleet.wait_for_arrival(nave.symbol)

    def _navegar_a_la_deriva(self, nave: Ship, destino: str):
        """Ultimo recurso: viajar en DRIFT y volver a CRUISE al llegar."""
        log.warning("sin combustible para el tramo; se va en DRIFT (lento pero llega)")
        self.fleet.set_flight_mode(nave.symbol, ShipNavFlightMode.drift)
        try:
            return self.fleet.navigate(nave.symbol, destino)
        except ApiError:
            # Si ni a la deriva se puede, se restaura el modo para no dejar la
            # nave configurada en DRIFT para siempre.
            self.fleet.set_flight_mode(nave.symbol, ShipNavFlightMode.cruise)
            raise

    def _orbitar(self, nave: Ship) -> None:
        # El estado se consulta a la API, no al objeto `nave`: entre que se leyo y
        # ahora el propio bot pudo haberla atracado para recargar, y navegar
        # atracado falla con 4236.
        actual = self.fleet.get_nav(nave.symbol)
        if str(actual.status) != "IN_ORBIT":
            self.fleet.orbit(nave.symbol)

    def _atracar(self, nave: Ship) -> None:
        actual = self.fleet.get_nav(nave.symbol)
        if str(actual.status) != "DOCKED":
            self.fleet.dock(nave.symbol)

    def recargar(self, nave: Ship) -> None:
        """Llena el tanque si no esta casi lleno. Silencioso si no se vende FUEL aca.

        Recargar exige estar atracado, asi que atraca antes si hace falta. El
        combustible es barato (unos cientos de creditos por tanque) comparado con
        quedarse tirado a mitad de camino, asi que conviene salir siempre lleno.
        """
        nave = self.fleet.get_ship(nave.symbol)
        if nave.fuel.capacity == 0:
            return  # las sondas no consumen combustible
        if nave.fuel.current / nave.fuel.capacity >= UMBRAL_DE_COMBUSTIBLE:
            return

        try:
            self._atracar(nave)
            resultado = self.fleet.refuel(nave.symbol)
            log.info(
                "recargado a %s/%s por %s creditos",
                resultado.fuel.current,
                resultado.fuel.capacity,
                f"{resultado.transaction.total_price:,}",
            )
        except ApiError as exc:
            log.warning("no se pudo recargar en %s: %s", nave.nav.waypoint_symbol, exc.message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m bots.contract_runner",
        description="Acepta, abastece, entrega y cumple contratos de aprovisionamiento.",
    )
    parser.add_argument("--ship", help="nave a usar (default: la de mayor bodega)")
    parser.add_argument(
        "--cycles", type=int, default=1, help="cuantos contratos trabajar seguidos"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="logs de debug")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        with Session.from_env() as sesion:
            ContractRunner(sesion, args.ship).run(cycles=args.cycles)
    except SpaceTradersError as exc:
        log.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        log.info("cancelado")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
