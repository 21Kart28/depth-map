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


def test_get_provider_follows_settings():
    fake = get_provider(Settings(_env_file=None, provider="fake"))
    real = get_provider(Settings(_env_file=None, provider="anthropic", model="some-model"))
    assert isinstance(fake, FakeProvider)
    assert isinstance(real, AnthropicProvider)
    assert real.model == "some-model"
