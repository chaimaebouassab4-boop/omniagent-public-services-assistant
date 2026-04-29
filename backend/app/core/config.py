from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Omniagent Public Services API"
    app_version: str = "1.0.0"
    database_url: str = Field(
        default="sqlite:///./omniagent.db",
        description="SQLAlchemy database URL"
    )
    jwt_secret_key: str = "dev-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    upload_root: str = "uploads"


settings = Settings()
