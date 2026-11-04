import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pika.exceptions import AMQPConnectionError

from app.messaging.consumer import RabbitMQConsumer
from app.messaging.handler import EventoInvalidoError

URL = "amqp://guest:guest@localhost:5672/%2F"


def _consumer(
    handler: MagicMock | None = None, factory: MagicMock | None = None
) -> RabbitMQConsumer:
    return RabbitMQConsumer(
        url=URL,
        exchange="pedidos",
        queue="entregador.pedidos",
        handler=handler or MagicMock(),
        connection_factory=factory or MagicMock(),
        retry_seconds=0.01,
    )


def _method(routing_key: str = "entrega.aceita") -> SimpleNamespace:
    return SimpleNamespace(routing_key=routing_key, delivery_tag=7)


def test_setup_declara_exchange_fila_e_binds_dos_eventos() -> None:
    channel = MagicMock()

    _consumer().setup(channel)

    channel.exchange_declare.assert_called_once_with(
        exchange="pedidos", exchange_type="topic", durable=True
    )
    channel.queue_declare.assert_called_once_with(queue="entregador.pedidos", durable=True)
    chaves = {chamada.kwargs["routing_key"] for chamada in channel.queue_bind.call_args_list}
    assert chaves == {"entrega.aceita", "pedido.entregue"}


def test_mensagem_processada_recebe_ack() -> None:
    handler, channel = MagicMock(), MagicMock()

    _consumer(handler).on_message(channel, _method(), None, b"{}")

    handler.handle.assert_called_once_with("entrega.aceita", b"{}")
    channel.basic_ack.assert_called_once_with(delivery_tag=7)


def test_mensagem_invalida_e_descartada_sem_requeue() -> None:
    handler, channel = MagicMock(), MagicMock()
    handler.handle.side_effect = EventoInvalidoError("ruim")

    _consumer(handler).on_message(channel, _method(), None, b"x")

    channel.basic_reject.assert_called_once_with(delivery_tag=7, requeue=False)
    channel.basic_ack.assert_not_called()


def test_falha_inesperada_devolve_para_a_fila() -> None:
    handler, channel = MagicMock(), MagicMock()
    handler.handle.side_effect = RuntimeError("banco fora")

    _consumer(handler).on_message(channel, _method(), None, b"{}")

    channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=True)
    channel.basic_ack.assert_not_called()


def test_consume_once_consome_e_fecha_a_conexao() -> None:
    factory = MagicMock()
    connection = factory.return_value
    channel = connection.channel.return_value
    connection.is_open = True
    consumer = _consumer(factory=factory)

    consumer.consume_once()

    channel.basic_consume.assert_called_once_with(
        queue="entregador.pedidos", on_message_callback=consumer.on_message
    )
    channel.start_consuming.assert_called_once()
    connection.close.assert_called_once()


def test_run_reconecta_depois_de_falha_ate_stop() -> None:
    factory = MagicMock()
    tentativas = []
    consumer = _consumer(factory=factory)

    def conectar(_params):
        tentativas.append(1)
        if len(tentativas) >= 3:
            consumer._stop.set()
        raise AMQPConnectionError("broker fora")

    factory.side_effect = conectar

    consumer.run()

    assert len(tentativas) == 3


def test_start_e_stop_param_a_thread_e_o_consumo() -> None:
    consumindo = threading.Event()
    liberar = threading.Event()
    factory = MagicMock()
    connection = factory.return_value
    connection.is_open = True
    channel = connection.channel.return_value

    def start_consuming():
        consumindo.set()
        liberar.wait(2)

    def callback_threadsafe(callback):
        callback()
        liberar.set()

    channel.start_consuming.side_effect = start_consuming
    connection.add_callback_threadsafe.side_effect = callback_threadsafe
    consumer = _consumer(factory=factory)

    consumer.start()
    assert consumindo.wait(2)
    consumer.stop(timeout=2)

    connection.add_callback_threadsafe.assert_called_once()
    channel.stop_consuming.assert_called_once()
    assert not consumer._thread.is_alive()


@pytest.mark.parametrize("conexao_aberta", [False, True])
def test_stop_sem_consumo_ativo_nao_falha(conexao_aberta: bool) -> None:
    consumer = _consumer()
    if conexao_aberta:
        consumer._connection = MagicMock(is_open=True)

    consumer.stop(timeout=0.1)

    assert consumer._stop.is_set()
