import pytest

from depthmap.codebook import load_codebook, parse_codebook


def make_code(**changes):
    code = {
        "id": "holding-back",
        "group": "interpersonal",
        "label": "Holding something back",
        "definition": "Wanted to say something to a person and did not.",
        "example": "I wanted to tell her and said it was fine.",
        "counter_example": "Waiting for a better time to bring it up.",
    }
    return code | changes


def test_codebook_loads_22_codes():
    codebook = load_codebook()
    assert len(codebook.codes) == 22
    assert codebook.version == "v1-placeholder"


def test_get_returns_code():
    codebook = load_codebook()
    assert codebook.get("holding-back").group == "interpersonal"
    assert codebook.get("no-such-code") is None


def test_duplicate_id_fails_with_the_id():
    data = {"version": "test", "codes": [make_code(), make_code()]}
    with pytest.raises(ValueError, match="holding-back: duplicate id"):
        parse_codebook(data)


def test_unknown_group_fails_with_the_id():
    data = {"version": "test", "codes": [make_code(group="diagnosis")]}
    with pytest.raises(ValueError, match="holding-back: unknown group"):
        parse_codebook(data)


@pytest.mark.parametrize("field", ["definition", "example", "counter_example"])
def test_blank_text_fails_with_the_id(field):
    data = {"version": "test", "codes": [make_code(**{field: " "})]}
    with pytest.raises(ValueError, match=f"holding-back: missing {field}"):
        parse_codebook(data)
