from typing import Any
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "Omniagent Public Services API"
    app_version: str = "1.0.0"
    database_url: str = Field(
        default="sqlite:///./omniagent.db",
        description="SQLAlchemy database URL"
    )
    jwt_secret_key: str = "dev-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
    upload_root: str = "uploads"
    admin_email: str = "admin@demo.local"
    admin_password: str = "admin123"
    debug_logging: bool = Field(
        default=False,
        description="Emit concise development-only chat pipeline traces",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # The LLM is server configuration; clients never select it per request.
    llm_provider: str = Field(default="ollama", description="ollama, openai, or gemini")

    ollama_model: str = Field(default="llama3.2:3b", description="Local Ollama model name")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    ollama_request_timeout: float = 360.0
    ollama_context_window: int = 8192

    openai_api_key: str = Field(default="", description="OpenAI API key for RAG LLM")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")

    google_api_key: str = Field(default="", description="Google Gemini API key for RAG LLM")
    gemini_model: str = Field(default="gemini-3.6-flash", description="Gemini model name")
    embedding_model: str = Field(default="BAAI/bge-m3", description="HuggingFace embedding model name")

    # ── Audio / Voice ──
    gemini_audio_model: str = Field(default="gemini-3.6-flash", description="Gemini model for audio transcription")
    max_audio_upload_bytes: int = Field(default=25 * 1024 * 1024, description="Max audio upload size in bytes (25 MB)")

    # ── OCR Engine (Tesseract) ──
    tesseract_cmd: str = Field(default="", description="Path to Tesseract OCR executable (or TESSERACT_CMD env)")
    tessdata_prefix: str = Field(default="", description="Path to tessdata folder (or TESSDATA_PREFIX env)")


settings = Settings()
