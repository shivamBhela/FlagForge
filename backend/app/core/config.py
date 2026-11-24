from typing import List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "FlagForge API"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "temporary-development-secret-key-change-in-production-min32chars"
    ENCRYPTION_KEY: str = "tU_hQ8z2fPj_eL7_X0v9Y4kW3rA6mB1nC5sD8eF2gH4="

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    DATABASE_URL: str = "sqlite+aiosqlite:///./flagforge.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    FLAGSMITH_BASE_URL: str = "https://edge.api.flagsmith.com/api/v1"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
