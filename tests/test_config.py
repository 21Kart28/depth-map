import pytest
from pydantic import ValidationError

from depthmap.config import Settings
from depthmap.providers import AnthropicProvider, FakeProvider, get_provider


def test_provider_is_fake_without_key(monkeypatch):
    monkeypatch.delenv("DEPTHMAP_PROVIDER")
    assert Settings(_env_file=None).provider == "fake"


def test_provider_is_anthropic_with_key(monkeypatch):
    monkeypatch.delenv("DEPTHMAP_PROVIDER")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert Settings(_env_file=None).provider == "anthropic"


def test_explicit_provider_wins_over_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert Settings(_env_file=None).provider == "fake"


def test_key_is_hidden_in_repr():
    settings = Settings(_env_file=None, anthropic_api_key="test-key")
    assert "test-key" not in repr(settings)


def test_log_level_is_upper_cased(monkeypatch):
    monkeypatch.setenv("DEPTHMAP_LOG_LEVEL", "info")
    assert Settings(_env_file=None).log_level == "INFO"
    assert Settings(_env_file=None, log_level="Debug").log_level == "DEBUG"


def test_unknown_log_level_is_rejected():
    with pytest.raises(ValidationError, match="unknown log level"):
        Settings(_env_file=None, log_level="loud")


def test_get_provider_follows_settings():
    fake = get_provider(Settings(_env_file=None, provider="fake"))
    real = get_provider(Settings(_env_file=None, provider="anthropic", model="some-model"))
    assert isinstance(fake, FakeProvider)
    assert isinstance(real, AnthropicProvider)
    assert real.model == "some-model"
