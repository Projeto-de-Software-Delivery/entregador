import logging
import threading
from collections.abc import Callable
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPError

from app.messaging.handler import STATUS_POR_EVENTO, EventoInvalidoError, EventoPedidoHandler

logger = logging.getLogger(__name__)

ConnectionFactory = Callable[[pika.URLParameters], BlockingConnection]


class RabbitMQConsumer:
    """
    Consome o exchange topic de pedidos numa fila propria do entregador, numa thread separada
    da API. Se o broker cair, tenta reconectar a cada ``retry_seconds`` ate ``stop()``.
    """

    def __init__(
        self,
        url: str,
        exchange: str,
        queue: str,
        handler: EventoPedidoHandler,
        connection_factory: ConnectionFactory = pika.BlockingConnection,
        retry_seconds: float = 5.0,
    ) -> None:
        self._parameters = pika.URLParameters(url)
        self._exchange = exchange
        self._queue = queue
        self._handler = handler
        self._connection_factory = connection_factory
        self._retry_seconds = retry_seconds
        self._stop = threading.Event()
        self._connection: BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._thread: threading.Thread | None = None

    def setup(self, channel: BlockingChannel) -> None:
        channel.exchange_declare(exchange=self._exchange, exchange_type="topic", durable=True)
        channel.queue_declare(queue=self._queue, durable=True)
        for routing_key in STATUS_POR_EVENTO:
            channel.queue_bind(queue=self._queue, exchange=self._exchange, routing_key=routing_key)
        channel.basic_qos(prefetch_count=10)

    def on_message(
        self, channel: BlockingChannel, method: Any, _properties: Any, body: bytes
    ) -> None:
        try:
            self._handler.handle(method.routing_key, body)
        except EventoInvalidoError as exc:
            # Reprocessar nao adianta: descarta para nao travar a fila.
            logger.error(
                "evento_descartado",
                extra={"routing_key": method.routing_key, "erro": str(exc)},
            )
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        except Exception:
            # Falha transitoria (ex.: banco fora): devolve para a fila e tenta de novo.
            logger.exception("evento_falhou", extra={"routing_key": method.routing_key})
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def consume_once(self) -> None:
        """Conecta, declara a topologia e consome ate a conexao cair ou ``stop()``."""
        connection = self._connection_factory(self._parameters)
        self._connection = connection
        try:
            channel = connection.channel()
            self._channel = channel
            self.setup(channel)
            channel.basic_consume(queue=self._queue, on_message_callback=self.on_message)
            logger.info("rabbitmq_consumindo", extra={"queue": self._queue})
            if not self._stop.is_set():
                channel.start_consuming()
        finally:
            self._channel = None
            self._connection = None
            if connection.is_open:
                connection.close()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self.consume_once()
            except AMQPError as exc:
                logger.warning("rabbitmq_indisponivel", extra={"erro": repr(exc)})
            self._stop.wait(self._retry_seconds)

    def start(self) -> None:
        self._thread = threading.Thread(target=self.run, name="rabbitmq-consumer", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        connection, channel = self._connection, self._channel
        if connection is not None and channel is not None and connection.is_open:
            # pika nao e thread-safe: pede para a thread do consumidor parar o loop.
            connection.add_callback_threadsafe(channel.stop_consuming)
        if self._thread is not None:
            self._thread.join(timeout)
