import json
from collections import Counter
from importlib import resources

from depthmap.models import Analysis, Question, QuestionV2

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


class QuestionBank:
    def __init__(self, questions: list[Question] | list[QuestionV2]):
        self.questions = questions
        self._by_id = {q.id: q for q in questions}

    def get(self, question_id: str) -> Question | QuestionV2 | None:
        return self._by_id.get(question_id)

    def next(
        self, history: list[str], enabled_gated: bool = False, pinned_id: str | None = None
    ) -> Question | QuestionV2:
        """Pick the next question from the ids answered so far, oldest first."""
        if pinned_id is not None:
            return self._by_id[pinned_id]
        counts = Counter(history)
        # min() returns the first of several equal items, so ties go in file order
        return min(self.allowed(history, enabled_gated), key=lambda q: counts[q.id])

    def allowed(self, history: list[str], enabled_gated: bool) -> list:
        return self.questions


class QuestionBankV2(QuestionBank):
    def allowed(self, history: list[str], enabled_gated: bool) -> list[QuestionV2]:
        ungated = [q for q in self.questions if enabled_gated or not q.clinician_gated]
        # the last id can be missing from this bank when the history was written on another one
        last = self.get(history[-1]) if history else None
        if last is None:
            return ungated
        rotated = [
            q
            for q in ungated
            if q.domain != last.domain and not (q.mode == last.mode == "disclosure")
        ]
        # a bank too small to rotate still has to return something
        return rotated or ungated


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
            if hook not in Analysis.model_fields:
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


def load_bank(version: str) -> QuestionBank:
    data = resources.files("depthmap") / "data"
    if version == "v2":
        items = json.loads((data / "questions.v2.json").read_text(encoding="utf-8"))
        return QuestionBankV2(parse_questions_v2(items))
    items = json.loads((data / "questions.json").read_text(encoding="utf-8"))
    return QuestionBank([Question(**item) for item in items])
