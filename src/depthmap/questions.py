import json
from importlib import resources

from depthmap.models import Question, QuestionV2

DOMAINS = {
    "relationship-episode",
    "situated-thought",
    "avoidance",
    "functioning",
    "emotion-in-context",
    "change-sustain",
    "went-well",
}
MODES = {"disclosure", "concrete", "positive"}
# the analysis fields a question can point at; the v2 analysis model is not written yet
SCHEMA_HOOKS = {
    "themes",
    "candidate_themes",
    "client_emotion",
    "tone",
    "relational_episode",
    "change_talk",
    "sustain_talk",
}


class QuestionBank:
    def __init__(self, questions: list[Question] | list[QuestionV2]):
        self.questions = questions
        self._by_id = {q.id: q for q in questions}

    def get(self, question_id: str) -> Question | QuestionV2 | None:
        return self._by_id.get(question_id)

    def next(self, counts: dict[str, int]) -> Question | QuestionV2:
        # min() returns the first of several equal items, so ties go in file order
        return min(self.questions, key=lambda q: counts.get(q.id, 0))


def parse_questions_v2(data: dict) -> list[QuestionV2]:
    """Check the shape of a v2 bank and build its questions, naming the one that is wrong."""
    questions = []
    seen = set()
    for item in data["questions"]:
        question_id = item["id"]
        if question_id in seen:
            raise ValueError(f"question {question_id}: duplicate id")
        seen.add(question_id)
        if item.get("domain") not in DOMAINS:
            raise ValueError(f"question {question_id}: unknown domain {item.get('domain')!r}")
        if item.get("mode") not in MODES:
            raise ValueError(f"question {question_id}: unknown mode {item.get('mode')!r}")
        for hook in item["schema_hooks"]:
            if hook not in SCHEMA_HOOKS:
                raise ValueError(f"question {question_id}: unknown schema hook {hook!r}")
        questions.append(
            QuestionV2(
                id=question_id,
                domain=item["domain"],
                mode=item["mode"],
                framing=item["framing"],
                text=item["question"],
                clinician_gated=item["clinician_gated"],
                schema_hooks=item["schema_hooks"],
            )
        )
    return questions


def load_bank(version: str = "v1") -> QuestionBank:
    data = resources.files("depthmap") / "data"
    if version == "v2":
        items = json.loads((data / "questions.v2.json").read_text(encoding="utf-8"))
        return QuestionBank(parse_questions_v2(items))
    items = json.loads((data / "questions.json").read_text(encoding="utf-8"))
    return QuestionBank([Question(**item) for item in items])
