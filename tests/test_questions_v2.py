import pytest
from fastapi.testclient import TestClient

from depthmap.api import create_app
from depthmap.config import Settings
from depthmap.providers import FakeProvider
from depthmap.questions import DOMAINS, MODES, load_bank, parse_questions_v2
from depthmap.store import InMemoryRepository


def make_question(**changes):
    question = {
        "id": "avoid-01",
        "domain": "avoidance",
        "mode": "concrete",
        "framing": "Most weeks have one thing that keeps sliding.",
        "question": "What did you put off this week, and what did you do instead?",
        "clinician_gated": False,
        "schema_hooks": ["themes"],
    }
    return question | changes


def test_bank_loads_23_questions():
    questions = load_bank("v2").questions
    assert len(questions) == 23


def test_domains_and_modes_are_known():
    questions = load_bank("v2").questions
    assert {q.domain for q in questions} == DOMAINS
    assert {q.mode for q in questions} == MODES


def test_gated_flags_are_read():
    gated = [q.id for q in load_bank("v2").questions if q.clinician_gated]
    assert gated == ["thought-04"]


def test_every_question_has_a_hook():
    for question in load_bank("v2").questions:
        assert question.schema_hooks


def test_framing_and_text_are_read():
    question = load_bank("v2").get("rel-ep-01")
    assert question.framing.endswith(".")
    assert question.text.endswith("?")


def test_v1_is_the_default_bank():
    assert len(load_bank().questions) == 14
    assert Settings(_env_file=None).question_bank == "v1"


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"domain": "dreams"}, "avoid-01: unknown domain"),
        ({"mode": "deep"}, "avoid-01: unknown mode"),
        ({"schema_hooks": ["mood_score"]}, "avoid-01: unknown schema hook"),
    ],
)
def test_bad_question_fails_with_the_id(changes, message):
    with pytest.raises(ValueError, match=message):
        parse_questions_v2({"questions": [make_question(**changes)]})


def test_duplicate_id_fails_with_the_id():
    with pytest.raises(ValueError, match="avoid-01: duplicate id"):
        parse_questions_v2({"questions": [make_question(), make_question()]})


def test_api_shows_framing_and_domain_on_v2():
    settings = Settings(_env_file=None, provider="fake", question_bank="v2")
    app = create_app(settings=settings, provider=FakeProvider(), repo=InMemoryRepository())
    client = TestClient(app)
    assert len(client.get("/questions").json()) == 23
    question = client.get("/questions/rel-ep-01").json()
    assert question["domain"] == "relationship-episode"
    assert question["framing"]
    created = client.post("/entries", json={"question_id": "rel-ep-01", "response": "We argued."})
    assert created.status_code == 201
