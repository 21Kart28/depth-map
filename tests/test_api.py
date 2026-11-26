from depthmap import __version__
from depthmap.providers import FakeProvider

ANSWER = "I kept avoiding the call with my landlord about the lease."


def post_entry(client, question_id="avoidance-01", response=ANSWER):
    return client.post("/entries", json={"question_id": question_id, "response": response})


def test_health_shape(client):
    reply = client.get("/health")
    assert reply.status_code == 200
    assert reply.json() == {"status": "ok", "version": __version__, "provider": "fake"}


def test_questions_count(client):
    assert len(client.get("/questions").json()) == 14


def test_get_question(client):
    reply = client.get("/questions/desire-01")
    assert reply.status_code == 200
    assert reply.json()["id"] == "desire-01"


def test_unknown_question_is_404(client):
    reply = client.get("/questions/no-such-id")
    assert reply.status_code == 404
    assert reply.json() == {"error": "not_found", "detail": "question not found"}


def test_next_rotates_after_a_post(client):
    first = client.get("/questions/next").json()
    assert post_entry(client, first["id"]).status_code == 201
    second = client.get("/questions/next").json()
    assert second["id"] != first["id"]


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
    assert entry["question_id"] == "avoidance-01"
    assert entry["client_id"] == "local"
    assert entry["provider"] == "fake"
    assert entry["prompt_version"] == "v1"
    assert entry["analysis"]["themes"] == ["kept", "avoiding", "call"]
    assert client.get(f"/entries/{entry['id']}").json() == entry


def test_unknown_entry_is_404(client):
    reply = client.get("/entries/no-such-id")
    assert reply.status_code == 404
    assert reply.json() == {"error": "not_found", "detail": "entry not found"}


def test_limit_returns_newest(client):
    post_entry(client, "avoidance-01")
    newest = post_entry(client, "desire-01").json()
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


def test_unparseable_reply_is_502(make_client):
    client = make_client(FakeProvider(raw="not json"))
    reply = post_entry(client)
    assert reply.status_code == 502
    assert reply.json()["error"] == "analysis_parse_error"
    assert "Invalid JSON" in reply.json()["detail"]
    assert client.get("/entries").json() == []


def test_unknown_route_uses_the_error_shape(client):
    reply = client.get("/no-such-route")
    assert reply.status_code == 404
    assert set(reply.json()) == {"error", "detail"}
