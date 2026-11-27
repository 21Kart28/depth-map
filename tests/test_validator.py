import logging

import pytest

from depthmap.analysis import AnalysisValidationError, analyze
from depthmap.codebook import load_codebook
from depthmap.models import AnalysisOutput
from depthmap.providers import FakeProvider
from depthmap.validator import CATEGORIES, find_violations, load_rules, parse_rules

QUESTION = "What did you put off this week?"
ANSWER = "I kept avoiding the call with my landlord about the lease."
CODEBOOK = load_codebook()
RULES = load_rules()


def make_output(reflection, follow_up="What happened right after that?"):
    return AnalysisOutput(
        themes=["putting-off-task"],
        candidate_themes=[],
        theme_confidence=[{"theme": "putting-off-task", "confidence": "low"}],
        tone={"valence": 0, "arousal": 0, "labels": ["flat"]},
        relational_episode=None,
        change_talk=None,
        sustain_talk=None,
        reflection=reflection,
        follow_up_question=follow_up,
    )


class CleanSecondTryProvider:
    name = "clean-second-try"

    def __init__(self):
        self.prompts = []

    def complete_json(self, system, user, schema):
        self.prompts.append(user)
        phrase = "You should call them today." if len(self.prompts) == 1 else None
        return FakeProvider(violations=phrase).complete_json(system, user, schema)


def test_shipped_rules_cover_every_category():
    assert {rule.category for rule in RULES} == CATEGORIES


def test_clean_reply_is_accepted():
    output = make_output("You wrote that you kept avoiding the call with your landlord.")
    assert find_violations(output, RULES, ANSWER) == []


@pytest.mark.parametrize(
    "phrase, category",
    [
        ("You should call the landlord and get it over with.", "advice"),
        ("That sounds like depression talking about the lease.", "diagnosis"),
        ("You'll be fine once the call with the landlord is done.", "reassurance"),
        ("Great job noticing that you avoided the landlord call.", "praise"),
        ("On March 3 you put off the call with your landlord.", "date"),
    ],
)
def test_each_category_is_rejected(phrase, category):
    violations = find_violations(make_output(phrase), RULES, ANSWER)
    assert [violation.category for violation in violations] == [category]


def test_follow_up_question_is_checked_too():
    output = make_output("You wrote that you kept avoiding the call.", "Have you tried calling?")
    assert [v.category for v in find_violations(output, RULES, ANSWER)] == ["advice"]


def test_date_from_the_answer_is_allowed():
    output = make_output("You wrote that the lease ends on March 3 and you have not called.")
    assert find_violations(output, RULES, "The lease ends on march 3.") == []
    assert len(find_violations(output, RULES, ANSWER)) == 1


def test_one_violation_per_rule():
    output = make_output("You should call. You need to call. Have you tried calling them?")
    assert len(find_violations(output, RULES, ANSWER)) == 1


def test_matched_rule_is_logged(caplog):
    caplog.set_level(logging.INFO, logger="depthmap.validator")
    find_violations(make_output("Great job noticing that you avoided the call."), RULES, ANSWER)
    assert "rule praise (praise) matched" in caplog.text


def test_unknown_category_fails_with_the_id():
    data = {"rules": [{"id": "tone", "category": "mood", "patterns": [], "message": "no"}]}
    with pytest.raises(ValueError, match="rule tone: unknown category"):
        parse_rules(data)


def test_bad_pattern_fails_with_the_id():
    data = {"rules": [{"id": "broken", "category": "praise", "patterns": ["("], "message": "no"}]}
    with pytest.raises(ValueError, match="rule broken: bad pattern"):
        parse_rules(data)


def test_retry_succeeds_when_second_reply_is_clean():
    provider = CleanSecondTryProvider()
    analysis = analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert len(provider.prompts) == 2
    assert "do not give advice" in provider.prompts[1]
    assert "do not give advice" not in provider.prompts[0]
    assert "should" not in analysis.reflection


def test_retry_fails_and_raises_with_violations():
    provider = FakeProvider(violations="You should call them today.")
    with pytest.raises(AnalysisValidationError) as raised:
        analyze(QUESTION, ANSWER, provider, CODEBOOK, RULES)
    assert provider.calls == 2
    assert [violation.rule_id for violation in raised.value.violations] == ["advice-second-person"]
    assert "You should call them today." in raised.value.raw


def test_advice_typed_into_the_answer_is_caught():
    provider = FakeProvider()
    with pytest.raises(AnalysisValidationError):
        analyze(QUESTION, "My sister said you should just move out.", provider, CODEBOOK, RULES)
