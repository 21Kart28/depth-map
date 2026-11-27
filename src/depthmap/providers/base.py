from typing import Protocol

from pydantic import BaseModel


class ProviderError(Exception):
    pass


class ProviderRefusal(ProviderError):
    def __init__(self):
        super().__init__("model refused to answer")


class LLMProvider(Protocol):
    """What analyze() needs from a model backend."""

    name: str

    def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> str: ...
