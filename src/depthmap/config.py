from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings read from the environment and from .env if there is one."""

    model_config = SettingsConfigDict(
        env_prefix="DEPTHMAP_", env_file=".env", extra="ignore", populate_by_name=True
    )

    anthropic_api_key: SecretStr | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    provider: Literal["fake", "anthropic"] | None = None
    model: str = "claude-haiku-5-5"
    timeout: float = 60.0
    log_level: str = "INFO"
    db_path: str = "./depthmap.db"
    question_bank: Literal["v1", "v2"] = "v1"

    @model_validator(mode="after")
    def default_provider(self):
        if self.provider is None:
            self.provider = "anthropic" if self.anthropic_api_key else "fake"
        return self
