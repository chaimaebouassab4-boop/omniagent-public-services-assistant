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
    admin_email: str = "admin@demo.local"
    admin_password: str = "admin123"

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


settings = Settings()
