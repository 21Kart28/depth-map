import json
import re

from pydantic import BaseModel

from depthmap.codebook import load_codebook
from depthmap.providers.base import ProviderError


class FakeProvider:
    """Offline stand-in that builds a reply from the answer text."""

    name = "fake"

    def __init__(self, fail: bool = False, raw: str | None = None, violations: str | None = None):
        self.fail = fail
        self.raw = raw
        # a phrase added to every reflection, for driving the output validator in tests
        self.violations = violations
        self.calls = 0
        self._code_ids = load_codebook().active_ids()

    def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> str:
        self.calls += 1
        if self.fail:
            raise ProviderError("provider failed: fake failure")
        if self.raw is not None:
            return self.raw

        answer = user.rsplit("Answer:", 1)[-1].strip()
        words = set(re.findall(r"[a-z']{4,}", answer.lower()))
        # a code is picked when one of the longer words in its id is in the answer
        themes = [code_id for code_id in self._code_ids if words & set(code_id.split("-"))][:4]
        if not themes:
            themes = [self._code_ids[len(answer) % len(self._code_ids)]]
        reflection = f'You wrote: "{answer[:300]}". This reply stays with those words.'
        if self.violations:
            reflection += f" {self.violations}"
        return json.dumps(
            {
                "themes": themes,
                "candidate_themes": [],
                "theme_confidence": [{"theme": theme, "confidence": "low"} for theme in themes],
                "tone": {"valence": 0.0, "arousal": 0.0, "labels": ["neutral"]},
                "relational_episode": None,
                "change_talk": None,
                "sustain_talk": None,
                "reflection": reflection,
                "follow_up_question": "What happened right after that?",
            }
        )
