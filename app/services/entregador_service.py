import logging
from uuid import UUID

from app.core.exceptions import EntregadorNotFoundError
from app.models.entregador import Entregador, StatusEntregadorEnum
from app.repositories.entregador_repository import EntregadorRepository
from app.schemas.entregador import EntregadorCreate, EntregadorStatusUpdate, EntregadorUpdate

logger = logging.getLogger(__name__)


class EntregadorService:
    def __init__(self, repository: EntregadorRepository) -> None:
        self._repository = repository

    def create_entregador(self, payload: EntregadorCreate) -> Entregador:
        entregador = Entregador(
            nome=payload.nome,
            veiculo=payload.veiculo,
            status=StatusEntregadorEnum.DISPONIVEL,
        )
        created = self._repository.create(entregador)
        logger.info("entregador_created", extra={"entregador_id": str(created.id)})
        return created

    def list_entregadores(self) -> list[Entregador]:
        return self._repository.list()

    def get_entregador(self, entregador_id: UUID) -> Entregador:
        return self._get_or_raise(entregador_id)

    def update_entregador(self, entregador_id: UUID, payload: EntregadorUpdate) -> Entregador:
        entregador = self._get_or_raise(entregador_id)
        entregador.nome = payload.nome
        entregador.veiculo = payload.veiculo

        updated = self._repository.save(entregador)
        logger.info("entregador_updated", extra={"entregador_id": str(updated.id)})
        return updated

    def delete_entregador(self, entregador_id: UUID) -> None:
        entregador = self._get_or_raise(entregador_id)
        self._repository.delete(entregador)
        logger.info("entregador_deleted", extra={"entregador_id": str(entregador_id)})

    def update_status(
        self,
        entregador_id: UUID,
        payload: EntregadorStatusUpdate,
    ) -> Entregador:
        entregador = self._get_or_raise(entregador_id)
        entregador.status = payload.status

        updated = self._repository.save(entregador)
        logger.info(
            "entregador_status_updated",
            extra={"entregador_id": str(updated.id), "status": updated.status.value},
        )
        return updated

    def _get_or_raise(self, entregador_id: UUID) -> Entregador:
        entregador = self._repository.get_by_id(entregador_id)
        if entregador is None:
            raise EntregadorNotFoundError(entregador_id)
        return entregador
