import json

import pytest

from depthmap.analysis import AnalysisParseError, analyze
from depthmap.providers import FakeProvider, ProviderError

QUESTION = "What did you put off this week?"
ANSWER = "I kept avoiding the call with my landlord about the lease."


class SecondTryProvider:
    name = "second-try"

    def __init__(self):
        self.calls = 0

    def complete_json(self, system, user, schema):
        self.calls += 1
        if self.calls == 1:
            return "not json"
        return FakeProvider().complete_json(system, user, schema)


def test_analyze_returns_analysis():
    provider = FakeProvider()
    analysis = analyze(QUESTION, ANSWER, provider)
    assert analysis.themes == ["kept", "avoiding", "call"]
    assert "landlord" in analysis.reflection
    assert analysis.follow_up_question.endswith("?")
    assert provider.calls == 1


def test_fake_output_is_deterministic():
    assert analyze(QUESTION, ANSWER, FakeProvider()) == analyze(QUESTION, ANSWER, FakeProvider())


def test_bad_json_retries_once_then_raises():
    provider = FakeProvider(raw="not json")
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, provider)
    assert provider.calls == 2
    assert raised.value.raw == "not json"


def test_retry_succeeds_on_second_reply():
    provider = SecondTryProvider()
    analysis = analyze(QUESTION, ANSWER, provider)
    assert provider.calls == 2
    assert analysis.themes


def test_schema_invalid_reply_raises():
    reply = analyze(QUESTION, ANSWER, FakeProvider()).model_dump()
    reply["follow_up_question"] = "Tell me more about the landlord."
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, FakeProvider(raw=json.dumps(reply)))
    assert "follow_up_question" in raised.value.problems[0]


def test_provider_error_propagates():
    provider = FakeProvider(fail=True)
    with pytest.raises(ProviderError):
        analyze(QUESTION, ANSWER, provider)
    assert provider.calls == 1
