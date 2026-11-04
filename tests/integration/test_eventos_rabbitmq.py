"""
Integracao com um RabbitMQ de verdade: publica no exchange do mesmo jeito que o pedidos-lojas
(Java) e confere que o entregador mudou de status no banco.

Roda quando RABBITMQ_TEST_URL esta definido (o CI sobe o broker); senao e pulado.
"""

import json
import os
import time
from uuid import uuid4

import pika
import pytest
from sqlalchemy.orm import Session

from app.messaging.consumer import RabbitMQConsumer
from app.messaging.handler import EventoPedidoHandler
from app.models.entregador import Entregador, StatusEntregadorEnum, VeiculoEnum
from tests.conftest import TestingSessionLocal

RABBITMQ_TEST_URL = os.getenv("RABBITMQ_TEST_URL")

pytestmark = pytest.mark.skipif(not RABBITMQ_TEST_URL, reason="RABBITMQ_TEST_URL nao definido")


def _com_canal(acao) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_TEST_URL))
    try:
        acao(connection.channel())
    finally:
        connection.close()


def _publicar(exchange: str, routing_key: str, entregador_id: str) -> None:
    corpo = json.dumps(
        {
            "eventId": str(uuid4()),
            "eventType": routing_key,
            "version": 1,
            "occurredAt": "2026-11-03T12:00:00Z",
            "data": {"pedidoId": "1", "entregaId": "e-1", "entregadorId": entregador_id},
        }
    )
    _com_canal(
        lambda channel: channel.basic_publish(
            exchange=exchange, routing_key=routing_key, body=corpo
        )
    )


def _esperar_status(db: Session, entregador_id, esperado: StatusEntregadorEnum) -> None:
    limite = time.monotonic() + 10
    while time.monotonic() < limite:
        db.expire_all()
        if db.get(Entregador, entregador_id).status == esperado:
            return
        time.sleep(0.1)
    pytest.fail(f"entregador nao chegou em {esperado}")


def test_eventos_publicados_no_broker_atualizam_o_entregador(db_session: Session) -> None:
    sufixo = uuid4().hex[:8]
    exchange, queue = f"pedidos-teste-{sufixo}", f"entregador-teste-{sufixo}"
    entregador = Entregador(
        nome="Joao", veiculo=VeiculoEnum.MOTO, status=StatusEntregadorEnum.DISPONIVEL
    )
    db_session.add(entregador)
    db_session.commit()

    consumer = RabbitMQConsumer(
        url=RABBITMQ_TEST_URL,
        exchange=exchange,
        queue=queue,
        handler=EventoPedidoHandler(TestingSessionLocal),
        retry_seconds=0.2,
    )
    consumer.start()
    try:
        # a fila so existe depois que o consumidor declara a topologia
        limite = time.monotonic() + 10
        while consumer._channel is None and time.monotonic() < limite:
            time.sleep(0.05)

        _publicar(exchange, "entrega.aceita", str(entregador.id))
        _esperar_status(db_session, entregador.id, StatusEntregadorEnum.EM_ENTREGA)

        _publicar(exchange, "pedido.entregue", str(entregador.id))
        _esperar_status(db_session, entregador.id, StatusEntregadorEnum.DISPONIVEL)
    finally:
        consumer.stop()

        def limpar(channel) -> None:
            channel.queue_delete(queue=queue)
            channel.exchange_delete(exchange=exchange)

        _com_canal(limpar)
