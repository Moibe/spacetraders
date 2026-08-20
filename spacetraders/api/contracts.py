"""Contratos: la fuente de ingresos del arranque."""

from __future__ import annotations

from collections.abc import Iterator

from ..models import Contract
from .base import ApiSection
from .results import ContractAgreement, ContractDelivery


class ContractsApi(ApiSection):
    """Endpoints `/my/contracts`.

    El ciclo de vida es: negociar o recibir -> aceptar (cobras el anticipo) ->
    entregar mercancia -> cumplir (cobras el resto), siempre antes de `deadline`.
    """

    def iter_contracts(self, *, limit: int = 20) -> Iterator[Contract]:
        return self.client.paginate("/my/contracts", model=Contract, limit=limit)

    def list_contracts(self, *, limit: int = 20) -> list[Contract]:
        return list(self.iter_contracts(limit=limit))

    def get_contract(self, contract_id: str) -> Contract:
        return self.client.get(f"/my/contracts/{contract_id}", model=Contract)

    def accept(self, contract_id: str) -> ContractAgreement:
        """Acepta el contrato y cobra el pago inicial."""
        data = self.client.post(f"/my/contracts/{contract_id}/accept")
        return ContractAgreement.model_validate(data)

    def deliver(
        self, contract_id: str, ship_symbol: str, trade_symbol: str, units: int
    ) -> ContractDelivery:
        """Entrega mercancia de la bodega de una nave atracada en el destino."""
        data = self.client.post(
            f"/my/contracts/{contract_id}/deliver",
            json={
                "shipSymbol": ship_symbol,
                "tradeSymbol": str(trade_symbol),
                "units": units,
            },
        )
        return ContractDelivery.model_validate(data)

    def fulfill(self, contract_id: str) -> ContractAgreement:
        """Cierra el contrato ya entregado y cobra el pago final."""
        data = self.client.post(f"/my/contracts/{contract_id}/fulfill")
        return ContractAgreement.model_validate(data)

    def negotiate(self, ship_symbol: str) -> Contract:
        """Consigue un contrato nuevo con una nave atracada en un waypoint con faccion."""
        data = self.client.post(f"/my/ships/{ship_symbol}/negotiate/contract")
        return Contract.model_validate(data["contract"])

    # ------------------------------------------------------------------ helpers

    def pending(self, *, limit: int = 20) -> list[Contract]:
        """Contratos aceptados que todavia no se cumplieron."""
        return [c for c in self.iter_contracts(limit=limit) if c.accepted and not c.fulfilled]

    def available(self, *, limit: int = 20) -> list[Contract]:
        """Contratos ofrecidos que todavia no se aceptaron."""
        return [c for c in self.iter_contracts(limit=limit) if not c.accepted]
