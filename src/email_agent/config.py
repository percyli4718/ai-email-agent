from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    # Ollama
    ollama_host: str = Field(default="localhost:11434", env="OLLAMA_HOST")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/email_agent.db",
        env="DATABASE_URL"
    )

    # ChromaDB
    chroma_persist_dir: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIR")

    # Application
    env: str = Field(default="development", env="ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Cost control
    default_agent_budget: float = Field(default=1.0, env="DEFAULT_AGENT_BUDGET")
    max_sonnet_cost_per_email: float = Field(default=0.02, env="MAX_SONNET_COST")
    max_opus_cost_per_email: float = Field(default=0.10, env="MAX_OPUS_COST")

    # Target Sonnet routing rate (80% per JD)
    target_sonnet_rate: float = Field(default=0.80, env="TARGET_SONNET_RATE")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI to inject settings."""
    return settings
