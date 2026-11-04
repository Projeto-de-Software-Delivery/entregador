from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import app.main as main
from app.core.config import Settings
from app.messaging.consumer import RabbitMQConsumer


def _settings(**valores) -> Settings:
    return Settings(database_url="sqlite+pysqlite:///:memory:", **valores)


def test_sem_rabbitmq_url_nao_cria_consumidor() -> None:
    assert main.build_consumer(_settings(rabbitmq_url="")) is None


def test_com_rabbitmq_url_cria_consumidor() -> None:
    consumer = main.build_consumer(_settings(rabbitmq_url="amqp://guest:guest@rabbit:5672/%2F"))

    assert isinstance(consumer, RabbitMQConsumer)


def test_lifespan_liga_e_desliga_o_consumidor(monkeypatch) -> None:
    consumer = MagicMock()
    monkeypatch.setattr(main, "build_consumer", lambda _settings: consumer)

    with TestClient(main.create_app()) as client:
        assert client.get("/health").status_code == 200
        consumer.start.assert_called_once()
        consumer.stop.assert_not_called()

    consumer.stop.assert_called_once()
