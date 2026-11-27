from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from anthropic.types import TextBlock, ThinkingBlock

from depthmap.models import AnalysisOutput
from depthmap.providers import AnthropicProvider, ProviderError, ProviderRefusal


class StubMessages:
    def __init__(self, content=None, error=None, stop_reason="end_turn"):
        self.content = content
        self.error = error
        self.stop_reason = stop_reason
        self.request = None

    def create(self, **request):
        self.request = request
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content, stop_reason=self.stop_reason)


def make_provider(content=None, error=None, stop_reason="end_turn"):
    messages = StubMessages(content, error, stop_reason)
    provider = AnthropicProvider(model="test-model", client=SimpleNamespace(messages=messages))
    return provider, messages


def test_request_shape_and_returned_text():
    provider, messages = make_provider([TextBlock(type="text", text='{"a": 1}')])
    assert (
        provider.complete_json("the system prompt", "the user text", AnalysisOutput) == '{"a": 1}'
    )

    request = messages.request
    assert request["model"] == "test-model"
    assert request["system"] == "the system prompt"
    assert request["messages"] == [{"role": "user", "content": "the user text"}]
    assert request["output_config"]["format"]["type"] == "json_schema"
    assert "reflection" in request["output_config"]["format"]["schema"]["properties"]
    assert "temperature" not in request


def test_text_is_found_after_a_thinking_block():
    thinking = ThinkingBlock(type="thinking", thinking="", signature="sig")
    provider, _ = make_provider([thinking, TextBlock(type="text", text="{}")])
    assert provider.complete_json("s", "u", AnalysisOutput) == "{}"


def test_empty_content_raises():
    provider, _ = make_provider([])
    with pytest.raises(ProviderError):
        provider.complete_json("s", "u", AnalysisOutput)


def test_refusal_raises_its_own_error():
    for content in ([TextBlock(type="text", text="I can't help with that.")], []):
        provider, _ = make_provider(content, stop_reason="refusal")
        with pytest.raises(ProviderRefusal, match="model refused to answer"):
            provider.complete_json("s", "u", AnalysisOutput)


def test_connection_error_is_wrapped():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    provider, _ = make_provider(error=anthropic.APIConnectionError(request=request))
    with pytest.raises(ProviderError) as raised:
        provider.complete_json("s", "u", AnalysisOutput)
    assert isinstance(raised.value.__cause__, anthropic.APIConnectionError)
