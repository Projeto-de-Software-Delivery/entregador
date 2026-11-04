import json
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.messaging.handler import EventoInvalidoError, EventoPedidoHandler
from app.models.entregador import Entregador, StatusEntregadorEnum, VeiculoEnum
from tests.conftest import TestingSessionLocal


def _evento(event_type: str, entregador_id: str) -> bytes:
    return json.dumps(
        {
            "eventId": str(uuid4()),
            "eventType": event_type,
            "version": 1,
            "occurredAt": "2026-11-03T12:00:00Z",
            "data": {"pedidoId": "1", "entregaId": "e-1", "entregadorId": entregador_id},
        }
    ).encode()


def _criar_entregador(db: Session, status: StatusEntregadorEnum) -> Entregador:
    entregador = Entregador(nome="Joao", veiculo=VeiculoEnum.MOTO, status=status)
    db.add(entregador)
    db.commit()
    db.refresh(entregador)
    return entregador


def _status(db: Session, entregador: Entregador) -> StatusEntregadorEnum:
    db.expire_all()
    return db.get(Entregador, entregador.id).status


@pytest.fixture()
def handler() -> EventoPedidoHandler:
    return EventoPedidoHandler(TestingSessionLocal)


def test_entrega_aceita_marca_em_entrega(db_session: Session, handler: EventoPedidoHandler) -> None:
    entregador = _criar_entregador(db_session, StatusEntregadorEnum.DISPONIVEL)

    aplicado = handler.handle("entrega.aceita", _evento("entrega.aceita", str(entregador.id)))

    assert aplicado is True
    assert _status(db_session, entregador) == StatusEntregadorEnum.EM_ENTREGA


def test_pedido_entregue_libera_o_entregador(
    db_session: Session, handler: EventoPedidoHandler
) -> None:
    entregador = _criar_entregador(db_session, StatusEntregadorEnum.EM_ENTREGA)

    aplicado = handler.handle("pedido.entregue", _evento("pedido.entregue", str(entregador.id)))

    assert aplicado is True
    assert _status(db_session, entregador) == StatusEntregadorEnum.DISPONIVEL


def test_evento_repetido_e_idempotente(db_session: Session, handler: EventoPedidoHandler) -> None:
    entregador = _criar_entregador(db_session, StatusEntregadorEnum.DISPONIVEL)
    corpo = _evento("entrega.aceita", str(entregador.id))

    handler.handle("entrega.aceita", corpo)
    handler.handle("entrega.aceita", corpo)

    assert _status(db_session, entregador) == StatusEntregadorEnum.EM_ENTREGA


def test_evento_que_nao_interessa_e_ignorado(
    db_session: Session, handler: EventoPedidoHandler
) -> None:
    entregador = _criar_entregador(db_session, StatusEntregadorEnum.DISPONIVEL)

    assert handler.handle("pedido.criado", b"qualquer coisa") is False
    assert _status(db_session, entregador) == StatusEntregadorEnum.DISPONIVEL


def test_entregador_inexistente_nao_falha(
    db_session: Session, handler: EventoPedidoHandler
) -> None:
    assert handler.handle("pedido.entregue", _evento("pedido.entregue", str(uuid4()))) is False


@pytest.mark.parametrize(
    "corpo",
    [
        b"nao e json",
        json.dumps({"data": {}}).encode(),
        json.dumps({"semData": True}).encode(),
        json.dumps({"data": {"entregadorId": "31"}}).encode(),
        json.dumps(["lista"]).encode(),
    ],
)
def test_evento_malformado_levanta_evento_invalido(
    db_session: Session, handler: EventoPedidoHandler, corpo: bytes
) -> None:
    with pytest.raises(EventoInvalidoError):
        handler.handle("entrega.aceita", corpo)
