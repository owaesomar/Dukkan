import json
from functools import lru_cache
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import Field, PostgresDsn, RedisDsn, TypeAdapter, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://dukkan:dukkan@localhost:5432/dukkan"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    log_level: str = "INFO"
    session_ttl_hours: int = Field(default=24 * 7, gt=0, le=24 * 90)
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=120)
    s3_bucket: str | None = None
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        return str(TypeAdapter(PostgresDsn).validate_python(value))

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        return str(TypeAdapter(RedisDsn).validate_python(value))

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        normalized = value.strip()
        if not normalized:
            return []
        if normalized.startswith("["):
            return json.loads(normalized)
        return [origin.strip() for origin in normalized.split(",") if origin.strip()]

    @field_validator("s3_bucket", "s3_endpoint_url", mode="before")
    @classmethod
    def normalize_optional_storage_setting(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "production"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of {sorted(allowed)}")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env != "production":
            return self
        if not self.cors_origins or any(
            not origin.startswith("https://") or "*" in origin for origin in self.cors_origins
        ):
            raise ValueError("Production CORS_ORIGINS must contain explicit HTTPS origins")
        for name, value in (("DATABASE_URL", self.database_url), ("REDIS_URL", self.redis_url)):
            hostname = urlsplit(value).hostname
            if hostname in {None, "localhost", "127.0.0.1", "::1"}:
                raise ValueError(f"{name} must point to a configured production service")
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET is required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
