from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Delivery Entregador API"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str
    # Vazio desliga o consumidor de eventos (ex.: testes e dev sem broker).
    rabbitmq_url: str = ""
    rabbitmq_exchange: str = "pedidos"
    rabbitmq_queue: str = "entregador.pedidos"

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
