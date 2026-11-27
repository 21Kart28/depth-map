from depthmap import __version__
from depthmap.codebook import load_codebook
from depthmap.providers import FakeProvider

ANSWER = "I kept avoiding the call with my landlord about the lease."


class CrashingProvider:
    name = "crashing"

    def complete_json(self, system, user, schema):
        raise RuntimeError("secret detail")


def post_entry(client, question_id="avoid-01", response=ANSWER):
    return client.post("/entries", json={"question_id": question_id, "response": response})


def test_health_shape(client):
    reply = client.get("/health")
    assert reply.status_code == 200
    assert reply.json() == {"status": "ok", "version": __version__, "provider": "fake"}


def test_questions_count(client):
    assert len(client.get("/questions").json()) == 23


def test_get_question(client):
    reply = client.get("/questions/change-01")
    assert reply.status_code == 200
    assert reply.json()["id"] == "change-01"


def test_unknown_question_is_404(client):
    reply = client.get("/questions/no-such-id")
    assert reply.status_code == 404
    assert reply.json() == {"error": "not_found", "detail": "question not found"}


def test_next_rotates_after_a_post(client):
    first = client.get("/questions/next").json()
    assert post_entry(client, first["id"]).status_code == 201
    second = client.get("/questions/next").json()
    assert second["id"] != first["id"]


def test_next_is_per_client(client):
    first = client.get("/questions/next").json()
    post_entry(client, first["id"])
    assert client.get("/questions/next").json() != first
    assert client.get("/questions/next", params={"client_id": "someone-else"}).json() == first


def test_post_unknown_question_is_404(client):
    reply = post_entry(client, "no-such-id")
    assert reply.status_code == 404
    assert reply.json()["error"] == "not_found"


def test_blank_response_is_422(client):
    for blank in ("", "   \n"):
        reply = post_entry(client, response=blank)
        assert reply.status_code == 422
        assert reply.json()["error"] == "validation_error"
        assert "response" in reply.json()["detail"]


def test_response_over_5000_chars_is_422(client):
    assert post_entry(client, response="a" * 5000).status_code == 201
    assert post_entry(client, response="a" * 5001).status_code == 422


def test_post_then_get_round_trip(client):
    created = post_entry(client)
    assert created.status_code == 201
    entry = created.json()
    assert entry["question_id"] == "avoid-01"
    assert entry["client_id"] == "local"
    assert entry["provider"] == "fake"
    assert entry["prompt_version"] == "v2"
    assert entry["codebook_version"] == load_codebook().version
    assert set(entry["analysis"]["themes"]) <= set(load_codebook().active_ids())
    assert entry["analysis"]["client_emotion"] is None
    assert client.get(f"/entries/{entry['id']}").json() == entry


def test_client_emotion_and_client_id_are_stored(client):
    body = {
        "question_id": "rel-ep-01",
        "response": ANSWER,
        "client_emotion": "cornered",
        "client_id": "someone-else",
    }
    entry = client.post("/entries", json=body).json()
    assert entry["analysis"]["client_emotion"] == "cornered"
    assert entry["client_id"] == "someone-else"
    assert client.get(f"/entries/{entry['id']}").json() == entry
    assert client.get("/questions/next").json()["id"] == "rel-ep-01"
    other = client.get("/questions/next", params={"client_id": "someone-else"}).json()
    assert other["id"] != "rel-ep-01"


def test_unknown_entry_is_404(client):
    reply = client.get("/entries/no-such-id")
    assert reply.status_code == 404
    assert reply.json() == {"error": "not_found", "detail": "entry not found"}


def test_limit_returns_newest(client):
    post_entry(client, "avoid-01")
    newest = post_entry(client, "change-01").json()
    assert len(client.get("/entries").json()) == 2
    assert client.get("/entries", params={"limit": 1}).json() == [newest]


def test_limit_out_of_range_is_422(client):
    assert client.get("/entries", params={"limit": 0}).status_code == 422


def test_provider_failure_is_502(make_client):
    client = make_client(FakeProvider(fail=True))
    reply = post_entry(client)
    assert reply.status_code == 502
    assert reply.json()["error"] == "provider_error"
    assert reply.json()["detail"].startswith("provider failed")
    assert client.get("/entries").json() == []


def test_refusal_is_502(make_client):
    client = make_client(FakeProvider(refuse=True))
    reply = post_entry(client)
    assert reply.status_code == 502
    assert reply.json() == {"error": "provider_refusal", "detail": "model refused to answer"}
    assert client.get("/entries").json() == []


def test_unparseable_reply_is_502(make_client):
    client = make_client(FakeProvider(raw="not json"))
    reply = post_entry(client)
    assert reply.status_code == 502
    assert reply.json()["error"] == "analysis_parse_error"
    assert reply.json()["detail"].startswith("Invalid JSON")
    assert client.get("/entries").json() == []


def test_rejected_reply_is_502(make_client):
    client = make_client(FakeProvider(violations="You should call them today."))
    reply = post_entry(client)
    assert reply.status_code == 502
    assert reply.json()["error"] == "analysis_validation_error"
    assert "advice" in reply.json()["detail"]
    assert client.get("/entries").json() == []


def test_crash_is_500_without_the_exception_text(make_client, caplog):
    client = make_client(CrashingProvider(), raise_server_exceptions=False)
    reply = post_entry(client)
    assert reply.status_code == 500
    assert reply.json() == {"error": "internal_error", "detail": "internal error"}
    assert "secret" not in reply.text
    assert "RuntimeError: secret detail" in caplog.text
    assert client.get("/entries").json() == []


def test_unknown_route_uses_the_error_shape(client):
    reply = client.get("/no-such-route")
    assert reply.status_code == 404
    assert set(reply.json()) == {"error", "detail"}
