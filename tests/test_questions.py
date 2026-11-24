from depthmap.questions import load_bank


def test_bank_loads_14_questions():
    assert len(load_bank().questions) == 14


def test_ids_are_unique():
    ids = [q.id for q in load_bank().questions]
    assert len(ids) == len(set(ids))


def test_get_returns_question():
    bank = load_bank()
    assert bank.get("desire-01") in bank.questions


def test_get_miss_returns_none():
    assert load_bank().get("no-such-id") is None


def test_next_prefers_least_answered():
    bank = load_bank()
    counts = {q.id: 1 for q in bank.questions}
    counts[bank.questions[5].id] = 0
    assert bank.next(counts) == bank.questions[5]


def test_next_breaks_ties_in_file_order():
    bank = load_bank()
    assert bank.next({}) == bank.questions[0]
    assert bank.next({bank.questions[0].id: 1}) == bank.questions[1]
