from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    # Anthropic API
    anthropic_api_key: str = Field(default="test-key")

    # Ollama
    ollama_host: str = Field(default="localhost:11434")

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./data/email_agent.db")

    # ChromaDB
    chroma_persist_dir: str = Field(default="./data/chroma")

    # Application
    env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Cost control
    default_agent_budget: float = Field(default=1.0)
    max_sonnet_cost_per_email: float = Field(default=0.02)
    max_opus_cost_per_email: float = Field(default=0.10)

    # Target Sonnet routing rate (80% per JD)
    target_sonnet_rate: float = Field(default=0.80)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI to inject settings."""
    return settings
