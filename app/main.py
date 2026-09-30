import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import EntregadorNotFoundError
from app.core.logging import configure_logging
from app.routers.entregador_router import router as entregador_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(title=settings.app_name, version="0.1.0")
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
