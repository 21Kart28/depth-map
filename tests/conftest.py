import pytest
from fastapi.testclient import TestClient

from depthmap.api import create_app
from depthmap.config import Settings
from depthmap.providers import FakeProvider
from depthmap.store import InMemoryRepository
from depthmap.store_sqlite import SQLiteRepository


@pytest.fixture(autouse=True)
def offline_env(monkeypatch):
    # the suite must never reach the real API, even from a shell that has a key
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DEPTHMAP_PROVIDER", "fake")


@pytest.fixture
def settings():
    return Settings(_env_file=None, provider="fake")


@pytest.fixture(params=["memory", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memory":
        return InMemoryRepository()
    return SQLiteRepository(str(tmp_path / "test.db"))


@pytest.fixture
def make_client(settings, repo):
    def make(provider=None):
        app = create_app(settings=settings, provider=provider or FakeProvider(), repo=repo)
        return TestClient(app)

    return make


@pytest.fixture
def client(make_client):
    return make_client()
