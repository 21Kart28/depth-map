from datetime import UTC, datetime, timedelta

from depthmap.models import Analysis, Entry

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def make_entry(question_id="avoidance-01", client_id="local", created_at=NOW):
    return Entry(
        client_id=client_id,
        question_id=question_id,
        question_text="What did you put off this week?",
        response="The call with my landlord.",
        created_at=created_at,
        analysis=Analysis(
            themes=["putting-off-task"],
            candidate_themes=["landlord"],
            theme_confidence=[{"theme": "putting-off-task", "confidence": "high"}],
            tone={"valence": -0.3, "arousal": 0.4, "labels": ["uneasy"]},
            relational_episode=None,
            change_talk=None,
            sustain_talk=None,
            reflection="You wrote that you put off the call with your landlord.",
            follow_up_question="What happened right after that?",
            client_emotion="dread",
            prompt_version="v2",
            codebook_version="test",
        ),
        prompt_version="v2",
        codebook_version="test",
        provider="fake",
    )


def test_add_then_get(repo):
    entry = repo.add(make_entry())
    assert repo.get(entry.id) == entry


def test_get_miss_returns_none(repo):
    assert repo.get("no-such-id") is None


def test_list_newest_first(repo):
    old = repo.add(make_entry(created_at=NOW))
    new = repo.add(make_entry(created_at=NOW + timedelta(minutes=5)))
    middle = repo.add(make_entry(created_at=NOW + timedelta(minutes=1)))
    assert repo.list() == [new, middle, old]


def test_list_breaks_time_ties_by_latest_insert(repo):
    first = repo.add(make_entry())
    second = repo.add(make_entry())
    assert repo.list() == [second, first]


def test_list_limit(repo):
    repo.add(make_entry(created_at=NOW))
    newest = repo.add(make_entry(created_at=NOW + timedelta(minutes=1)))
    assert repo.list(limit=1) == [newest]


def test_list_is_per_client(repo):
    mine = repo.add(make_entry())
    theirs = repo.add(make_entry(client_id="someone-else"))
    assert repo.list() == [mine]
    assert repo.list("someone-else") == [theirs]


def test_list_limit_counts_one_client_only(repo):
    mine = repo.add(make_entry(created_at=NOW))
    repo.add(make_entry(client_id="someone-else", created_at=NOW + timedelta(minutes=1)))
    assert repo.list(limit=1) == [mine]


def test_question_history_is_oldest_first(repo):
    repo.add(make_entry("desire-01", created_at=NOW + timedelta(minutes=1)))
    repo.add(make_entry("avoidance-01", created_at=NOW))
    repo.add(make_entry("avoidance-02", created_at=NOW + timedelta(minutes=1)))
    assert repo.question_history("local") == ["avoidance-01", "desire-01", "avoidance-02"]


def test_question_history_ignores_other_clients(repo):
    repo.add(make_entry("avoidance-01"))
    repo.add(make_entry("desire-01", client_id="someone-else"))
    repo.add(make_entry("avoidance-01"))
    assert repo.question_history("local") == ["avoidance-01", "avoidance-01"]


def test_entry_defaults():
    entry = make_entry()
    assert entry.client_id == "local"
    assert entry.created_at.tzinfo is not None
    assert entry.id != make_entry().id
