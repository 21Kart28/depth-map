from depthmap.questions import load_bank


def test_bank_loads_14_questions():
    assert len(load_bank("v1").questions) == 14


def test_ids_are_unique():
    ids = [q.id for q in load_bank("v1").questions]
    assert len(ids) == len(set(ids))


def test_get_returns_question():
    bank = load_bank("v1")
    assert bank.get("desire-01") in bank.questions


def test_get_miss_returns_none():
    assert load_bank("v1").get("no-such-id") is None


def test_next_prefers_least_answered():
    bank = load_bank("v1")
    history = [q.id for q in bank.questions if q != bank.questions[5]]
    assert bank.next(history) == bank.questions[5]


def test_next_breaks_ties_in_file_order():
    bank = load_bank("v1")
    assert bank.next([]) == bank.questions[0]
    assert bank.next([bank.questions[0].id]) == bank.questions[1]
