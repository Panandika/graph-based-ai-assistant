from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "graph_ai"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.OPENAI
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    default_model: str = "gpt-4o-mini"

    # LangGraph
    langgraph_checkpoint_collection: str = "langgraph_checkpoints"

    # File Upload Configuration
    upload_dir: str = "./uploads"
    upload_max_size_mb: int = 10
    upload_allowed_types: list[str] = [
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    ]
    upload_url_base: str = "http://localhost:8000/uploads"

    # Canva MCP Configuration
    canva_mcp_enabled: bool = True
    canva_mcp_timeout: int = 30000


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
