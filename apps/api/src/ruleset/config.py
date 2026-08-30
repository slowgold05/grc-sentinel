from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated process configuration loaded from the repository .env file."""

    database_url: PostgresDsn
    migration_database_url: PostgresDsn
    voyage_api_key: SecretStr | None = None
    voyage_embedding_model: str = "voyage-4-lite"
    upload_master_key_base64: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    anthropic_generation_model: str = "claude-sonnet-5"
    anthropic_verifier_model: str = "claude-haiku-4-5-20251001"
    clerk_secret_key: SecretStr | None = None
    clerk_jwt_key: SecretStr | None = None
    clerk_authorized_parties: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[4] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
