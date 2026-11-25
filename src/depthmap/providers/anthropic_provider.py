import anthropic
from pydantic import BaseModel

from depthmap.providers.base import ProviderError


class AnthropicProvider:
    """Calls the Messages API and asks for JSON in the shape of the schema."""

    name = "anthropic"

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        timeout: float = 60.0,
        client: anthropic.Anthropic | None = None,
    ):
        self.model = model
        self._api_key = api_key
        self._timeout = timeout
        self._client = client

    def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> str:
        try:
            if self._client is None:
                self._client = anthropic.Anthropic(api_key=self._api_key, timeout=self._timeout)
            # messages.parse() would validate the reply inside the SDK and drop the raw text
            # on failure, so the schema goes in output_config and analyze() validates
            message = self._client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={
                    "format": {"type": "json_schema", "schema": anthropic.transform_schema(schema)}
                },
            )
        except anthropic.AnthropicError as error:
            raise ProviderError(f"provider failed: {error}") from error

        # thinking blocks can come before the text block
        text = next((block.text for block in message.content if block.type == "text"), "")
        if not text:
            raise ProviderError("provider returned no text")
        return text
