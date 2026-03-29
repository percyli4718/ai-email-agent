import pytest
from email_agent.config import Settings


def test_settings_defaults(monkeypatch):
    """Test settings default values."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    settings = Settings()

    assert settings.anthropic_api_key == "test-key"
    assert settings.ollama_host == "localhost:11434"
    assert settings.target_sonnet_rate == 0.80
