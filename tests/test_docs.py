def test_docs_page_has_the_dark_mode_switch(client):
    reply = client.get("/docs")
    assert reply.status_code == 200
    assert "swagger-ui" in reply.text
    assert "theme-toggle" in reply.text
    assert "dark-mode" in reply.text


def test_docs_page_is_not_listed_as_a_route(client):
    assert "/docs" not in client.get("/openapi.json").json()["paths"]
