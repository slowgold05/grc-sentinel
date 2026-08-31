from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated process configuration loaded from the repository .env file."""

    database_url: PostgresDsn
    migration_database_url: PostgresDsn
    ollama_base_url: str = "http://localhost:11434/v1"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: SecretStr | None = None
    llm_generation_model: str = "qwen3:14b"
    llm_verifier_model: str = "qwen3:14b"
    ollama_embedding_model: str = "mxbai-embed-large"
    upload_master_key_base64: SecretStr | None = None
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
