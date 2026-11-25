import pytest


@pytest.fixture(autouse=True)
def offline_env(monkeypatch):
    # the suite must never reach the real API, even from a shell that has a key
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DEPTHMAP_PROVIDER", "fake")
