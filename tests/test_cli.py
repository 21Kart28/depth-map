import pytest

from depthmap.cli import main
from depthmap.codebook import load_codebook
from depthmap.providers import FakeProvider
from depthmap.questions import load_bank
from depthmap.store_sqlite import SQLiteRepository

ANSWER = "I kept avoiding the call with my landlord about the lease."
BANK = load_bank("v2")


@pytest.fixture
def stored(monkeypatch, tmp_path):
    # run from an empty folder so a .env next to the code is not read
    monkeypatch.chdir(tmp_path)
    path = str(tmp_path / "cli.db")
    monkeypatch.setenv("DEPTHMAP_DB_PATH", path)
    return SQLiteRepository(path)


@pytest.fixture
def run(monkeypatch, capsys, stored):
    def run(answers, *args, provider=None):
        replies = iter(answers)
        monkeypatch.setattr("builtins.input", lambda prompt: next(replies))
        monkeypatch.setattr("sys.argv", ["depthmap", *args])
        if provider:
            monkeypatch.setattr("depthmap.cli.get_provider", lambda settings: provider)
        main()
        return capsys.readouterr().out

    return run


def test_answer_is_stored_and_themes_printed(run, stored):
    out = run([ANSWER, "q"])
    first = BANK.next([])
    assert "Provider: fake" in out
    assert "Entries so far: 0" in out
    assert first.framing in out
    assert first.text in out

    entries = stored.list()
    assert len(entries) == 1
    assert entries[0].question_id == first.id
    assert entries[0].response == ANSWER
    codebook = load_codebook()
    for theme in entries[0].analysis.themes:
        assert f"  - {theme}: {codebook.get(theme).label}" in out


def test_second_run_counts_the_first(run):
    run([ANSWER, "q"])
    assert "Entries so far: 1" in run(["q"])


def test_question_id_pins_the_first_question(run, stored):
    pinned = BANK.questions[-1]
    assert pinned != BANK.next([])
    out = run([ANSWER, "q"], "--question-id", pinned.id)
    assert pinned.text in out
    assert stored.list()[0].question_id == pinned.id


def test_quit_stores_nothing(run, stored):
    run(["q"])
    assert stored.list() == []


def test_blank_answer_stores_nothing(run, stored):
    run(["", "   ", "q"])
    assert stored.list() == []


def test_unparsable_reply_prints_the_problems(run, stored):
    out = run([ANSWER, "q"], provider=FakeProvider(raw="not json"))
    assert "the analysis didn't pass validation:" in out
    assert "Invalid JSON" in out
    assert stored.list() == []


def test_rejected_reply_prints_the_rules(run, stored):
    out = run([ANSWER, "q"], provider=FakeProvider(violations="You should call them today."))
    assert "the analysis was rejected:" in out
    assert "advice" in out
    assert stored.list() == []


def test_provider_error_is_printed(run, stored):
    out = run([ANSWER, "q"], provider=FakeProvider(fail=True))
    assert "provider failed: fake failure" in out
    assert stored.list() == []
