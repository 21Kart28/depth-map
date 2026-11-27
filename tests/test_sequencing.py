import pytest

from depthmap.models import QuestionV2
from depthmap.questions import QuestionBankV2, load_bank


def make_question(question_id, domain, mode, gated=False):
    return QuestionV2(
        id=question_id,
        domain=domain,
        mode=mode,
        framing="A framing line.",
        text="A question?",
        clinician_gated=gated,
        schema_hooks=["themes"],
    )


BANK = QuestionBankV2(
    [
        make_question("a1", "avoidance", "disclosure"),
        make_question("a2", "avoidance", "concrete"),
        make_question("b1", "functioning", "disclosure"),
        make_question("b2", "functioning", "concrete"),
        make_question("g1", "situated-thought", "concrete", gated=True),
        make_question("c1", "went-well", "positive"),
    ]
)

CASES = [
    ("empty history starts in file order", [], {}, "a1"),
    ("pinned wins", ["a1"], {"pinned_id": "c1"}, "c1"),
    ("no two disclosures in a row", ["a1"], {}, "b2"),
    ("no two from the same domain in a row", ["a2"], {}, "b1"),
    ("gated is skipped", ["a1", "a2", "b1", "b2", "c1"], {}, "a1"),
    ("gated is served when enabled", ["a1", "a2", "b1", "b2", "c1"], {"enabled_gated": True}, "g1"),
    ("least answered wins", ["a1", "b2", "b2", "c1"], {}, "a2"),
    ("ties go in file order", ["c1"], {}, "a1"),
    ("all-disclosure history", ["a1", "b1", "a1", "b1"], {}, "a2"),
    ("unanswered domain waits its turn", ["b2", "c1", "b1", "c1", "a2"], {}, "b1"),
    ("enabled gated still follows rotation", ["a1"], {"enabled_gated": True}, "b2"),
    ("pinned overrides rotation and gating", ["a2"], {"pinned_id": "g1"}, "g1"),
    ("history from another bank is ignored", ["no-such-id"], {}, "a1"),
]


@pytest.mark.parametrize("name, history, flags, expected", CASES, ids=[c[0] for c in CASES])
def test_next(name, history, flags, expected):
    assert BANK.next(history, **flags).id == expected


def test_next_does_not_change_the_history():
    history = ["a1", "b2"]
    BANK.next(history)
    assert history == ["a1", "b2"]


def test_one_domain_bank_still_returns_a_question():
    bank = QuestionBankV2(
        [
            make_question("a1", "avoidance", "disclosure"),
            make_question("a2", "avoidance", "concrete"),
        ]
    )
    assert bank.next(["a1"]).id == "a2"


@pytest.mark.parametrize("enabled_gated", [False, True])
def test_50_picks_never_repeat_disclosure_or_domain(enabled_gated):
    bank = load_bank("v2")
    history = []
    previous = None
    for _ in range(50):
        question = bank.next(history, enabled_gated=enabled_gated)
        assert enabled_gated or not question.clinician_gated
        if previous is not None:
            assert question.domain != previous.domain
            assert not (question.mode == previous.mode == "disclosure")
        history.append(question.id)
        previous = question
    assert len(set(history)) > 10
