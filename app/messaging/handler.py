import json
import logging
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import EntregadorNotFoundError
from app.models.entregador import StatusEntregadorEnum
from app.repositories.entregador_repository import EntregadorRepository
from app.schemas.entregador import EntregadorStatusUpdate
from app.services.entregador_service import EntregadorService

logger = logging.getLogger(__name__)

# Eventos publicados pelo pedidos-lojas no exchange "pedidos" (routing key = eventType)
# e o status que o entregador assume quando cada um acontece.
STATUS_POR_EVENTO: dict[str, StatusEntregadorEnum] = {
    "entrega.aceita": StatusEntregadorEnum.EM_ENTREGA,
    "pedido.entregue": StatusEntregadorEnum.DISPONIVEL,
}


class EventoInvalidoError(ValueError):
    """Mensagem que nunca vai poder ser processada (JSON ruim, campo faltando, id invalido)."""


class EventoPedidoHandler:
    """Aplica no banco do entregador os eventos de pedido recebidos pelo RabbitMQ."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def handle(self, routing_key: str, body: bytes) -> bool:
        """Retorna True se o status de algum entregador foi alterado."""
        novo_status = STATUS_POR_EVENTO.get(routing_key)
        if novo_status is None:
            logger.debug("evento_ignorado", extra={"routing_key": routing_key})
            return False

        entregador_id = self._extrair_entregador_id(body)
        with self._session_factory() as db:
            service = EntregadorService(EntregadorRepository(db))
            try:
                service.update_status(entregador_id, EntregadorStatusUpdate(status=novo_status))
            except EntregadorNotFoundError:
                logger.warning(
                    "evento_entregador_inexistente",
                    extra={"routing_key": routing_key, "entregador_id": str(entregador_id)},
                )
                return False

        logger.info(
            "evento_aplicado",
            extra={
                "routing_key": routing_key,
                "entregador_id": str(entregador_id),
                "status": novo_status.value,
            },
        )
        return True

    @staticmethod
    def _extrair_entregador_id(body: bytes) -> UUID:
        try:
            evento = json.loads(body)
            return UUID(str(evento["data"]["entregadorId"]))
        except (ValueError, KeyError, TypeError) as exc:
            raise EventoInvalidoError(f"evento sem entregadorId valido: {exc}") from exc
