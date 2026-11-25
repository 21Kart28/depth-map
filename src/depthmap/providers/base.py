from typing import Protocol

from pydantic import BaseModel


class ProviderError(Exception):
    pass


class LLMProvider(Protocol):
    """What analyze() needs from a model backend."""

    name: str

    def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> str: ...
