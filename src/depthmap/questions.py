import json
from importlib import resources

from depthmap.models import Question


class QuestionBank:
    def __init__(self, questions: list[Question]):
        self.questions = questions
        self._by_id = {q.id: q for q in questions}

    def get(self, question_id: str) -> Question | None:
        return self._by_id.get(question_id)

    def next(self, counts: dict[str, int]) -> Question:
        # min() returns the first of several equal items, so ties go in file order
        return min(self.questions, key=lambda q: counts.get(q.id, 0))


def load_bank() -> QuestionBank:
    path = resources.files("depthmap") / "data" / "questions.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    return QuestionBank([Question(**item) for item in items])
