import json

import pytest

from depthmap.analysis import AnalysisParseError, analyze
from depthmap.codebook import load_codebook
from depthmap.prompts.analysis import ANALYSIS_PROMPT_VERSION, build_system_prompt
from depthmap.providers import FakeProvider, ProviderError
from depthmap.validator import load_rules

QUESTION = "What did you put off this week?"
ANSWER = "I kept avoiding the call with my landlord about the lease."
CODEBOOK = load_codebook()
RULES = load_rules()


def fake_reply(**changes):
    reply = json.loads(FakeProvider().complete_json("", f"Answer: {ANSWER}", None))
    return json.dumps(reply | changes)


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
    analysis = analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert 1 <= len(analysis.themes) <= 4
    assert set(analysis.themes) <= set(CODEBOOK.active_ids())
    assert [item.theme for item in analysis.theme_confidence] == analysis.themes
    assert "landlord" in analysis.reflection
    assert analysis.follow_up_question.endswith("?")
    assert analysis.prompt_version == ANALYSIS_PROMPT_VERSION == "v2"
    assert analysis.codebook_version == CODEBOOK.version
    assert provider.calls == 1


def test_fake_output_is_deterministic():
    first = analyze(QUESTION, ANSWER, FakeProvider(), CODEBOOK, RULES)
    assert first == analyze(QUESTION, ANSWER, FakeProvider(), CODEBOOK, RULES)


def test_bad_json_retries_once_then_raises():
    provider = FakeProvider(raw="not json")
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert provider.calls == 2
    assert raised.value.raw == "not json"


def test_retry_succeeds_on_second_reply():
    provider = SecondTryProvider()
    analysis = analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert provider.calls == 2
    assert analysis.themes


def test_follow_up_without_question_mark_is_rejected():
    provider = FakeProvider(raw=fake_reply(follow_up_question="Tell me more about the landlord."))
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert "follow_up_question" in raised.value.problems[0]


def test_unknown_theme_id_is_rejected():
    reply = fake_reply(
        themes=["shadow-work"], theme_confidence=[{"theme": "shadow-work", "confidence": "high"}]
    )
    provider = FakeProvider(raw=reply)
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert raised.value.problems == ["themes: unknown id shadow-work"]
    assert provider.calls == 2


def test_five_themes_are_rejected():
    five = CODEBOOK.active_ids()[:5]
    reply = fake_reply(
        themes=five, theme_confidence=[{"theme": theme, "confidence": "low"} for theme in five]
    )
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, FakeProvider(raw=reply), CODEBOOK, RULES)
    assert raised.value.problems[0].startswith("themes:")


def test_confidence_for_another_theme_is_rejected():
    reply = fake_reply(theme_confidence=[{"theme": "went-well", "confidence": "low"}])
    with pytest.raises(AnalysisParseError) as raised:
        analyze(QUESTION, ANSWER, FakeProvider(raw=reply), CODEBOOK, RULES)
    assert "theme_confidence" in raised.value.problems[0]


def test_client_emotion_passes_through_untouched():
    reply = fake_reply(client_emotion="calm")
    analysis = analyze(QUESTION, ANSWER, FakeProvider(raw=reply), CODEBOOK, RULES, " Gutted ")
    assert analysis.client_emotion == " Gutted "
    assert (
        analyze(QUESTION, ANSWER, FakeProvider(raw=reply), CODEBOOK, RULES).client_emotion is None
    )


def test_provider_error_propagates():
    provider = FakeProvider(fail=True)
    with pytest.raises(ProviderError):
        analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert provider.calls == 1


def test_prompt_lists_every_code():
    prompt = build_system_prompt(CODEBOOK)
    for code in CODEBOOK.codes:
        assert f"{code.id}: {code.definition}" in prompt


def test_prompt_has_no_warmth_words():
    prompt = build_system_prompt(CODEBOOK).lower()
    for word in ("warm", "supportive", "empathetic", "compassionate"):
        assert word not in prompt
