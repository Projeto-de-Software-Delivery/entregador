from uuid import UUID


class DomainError(Exception):
    """Base exception for domain-level errors."""


class EntregadorNotFoundError(DomainError):
    def __init__(self, entregador_id: UUID) -> None:
        super().__init__(f"Entregador {entregador_id} nao encontrado.")
        self.entregador_id = entregador_id
