import base64
from typing import List
from pydantic import AnyHttpUrl, field_validator, model_validator
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

    # Management API host (the edge.api.flagsmith.com host serves SDK evaluations).
    FLAGSMITH_BASE_URL: str = "https://api.flagsmith.com/api/v1"
    FLAGSMITH_ALLOWED_HOSTS: List[str] = []
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"
    OTEL_INGEST_TOKEN: str = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("FLAGSMITH_ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_flagsmith_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip().lower().rstrip(".") for host in v.split(",") if host.strip()]
        return v

    @model_validator(mode="after")
    def require_production_secrets(self):
        if self.APP_ENV.lower() not in {"prod", "production"}:
            return self

        known_secret_defaults = {
            "temporary-development-secret-key-change-in-production-min32chars",
            "default_secret_key_change_in_production",
        }
        if len(self.SECRET_KEY) < 32 or self.SECRET_KEY in known_secret_defaults:
            raise ValueError("Production requires a unique SECRET_KEY of at least 32 characters.")

        try:
            encryption_key = base64.urlsafe_b64decode(self.ENCRYPTION_KEY.encode("utf-8"))
        except Exception as exc:
            raise ValueError("Production requires a valid Fernet ENCRYPTION_KEY.") from exc
        if len(encryption_key) != 32 or self.ENCRYPTION_KEY == "tU_hQ8z2fPj_eL7_X0v9Y4kW3rA6mB1nC5sD8eF2gH4=":
            raise ValueError("Production requires a unique Fernet ENCRYPTION_KEY.")
        if len(self.OTEL_INGEST_TOKEN) < 32:
            raise ValueError("Production requires an OTEL_INGEST_TOKEN of at least 32 characters.")

        return self


settings = Settings()
