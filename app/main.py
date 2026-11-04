import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.exceptions import EntregadorNotFoundError
from app.core.logging import configure_logging
from app.messaging.consumer import RabbitMQConsumer
from app.messaging.handler import EventoPedidoHandler
from app.routers.entregador_router import router as entregador_router

logger = logging.getLogger(__name__)


def build_consumer(settings: Settings) -> RabbitMQConsumer | None:
    """Consumidor dos eventos de pedido, ou None quando RABBITMQ_URL nao esta definido."""
    if not settings.rabbitmq_url:
        logger.info("rabbitmq_desligado")
        return None
    from app.database.session import SessionLocal

    return RabbitMQConsumer(
        url=settings.rabbitmq_url,
        exchange=settings.rabbitmq_exchange,
        queue=settings.rabbitmq_queue,
        handler=EventoPedidoHandler(SessionLocal),
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        consumer = build_consumer(settings)
        if consumer is not None:
            consumer.start()
        try:
            yield
        finally:
            if consumer is not None:
                consumer.stop()

    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    application.include_router(entregador_router)
    register_exception_handlers(application)

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    logger.info("application_configured", extra={"environment": settings.environment})
    return application


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(EntregadorNotFoundError)
    async def entregador_not_found_handler(
        _request: Request,
        exc: EntregadorNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


app = create_app()
