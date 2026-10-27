import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_settings_require_remote_services_and_https_origins() -> None:
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://app:secret@postgres.example.net:5432/dukkan",
        redis_url="rediss://cache.example.net:6380/0",
        cors_origins=["https://shop.example.net"],
        s3_bucket="dukkan-media",
    )

    assert settings.app_env == "production"


@pytest.mark.parametrize(
    "changes",
    [
        {"database_url": "postgresql+psycopg://app:secret@localhost:5432/dukkan"},
        {"cors_origins": ["*"]},
    ],
)
def test_production_settings_reject_unsafe_or_missing_configuration(
    changes: dict[str, object],
) -> None:
    production_values: dict[str, object] = {
        "app_env": "production",
        "database_url": "postgresql+psycopg://app:secret@postgres.example.net:5432/dukkan",
        "redis_url": "rediss://cache.example.net:6380/0",
        "cors_origins": ["https://shop.example.net"],
        "s3_bucket": "dukkan-media",
    }
    production_values.update(changes)

    with pytest.raises(ValidationError):
        Settings(**production_values)  # type: ignore[arg-type]
