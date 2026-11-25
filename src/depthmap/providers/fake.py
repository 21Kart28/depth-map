import json
import re

from pydantic import BaseModel

from depthmap.providers.base import ProviderError


class FakeProvider:
    """Offline stand-in that builds a reply from the answer text."""

    name = "fake"

    def __init__(self, fail: bool = False, raw: str | None = None):
        self.fail = fail
        self.raw = raw
        self.calls = 0

    def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> str:
        self.calls += 1
        if self.fail:
            raise ProviderError("provider failed: fake failure")
        if self.raw is not None:
            return self.raw

        answer = user.rsplit("Answer:", 1)[-1].strip()
        words = re.findall(r"[a-z']{4,}", answer.lower())
        # dict.fromkeys drops repeats and keeps the order the words were written in
        themes = list(dict.fromkeys(words))[:3] or ["no answer"]
        return json.dumps(
            {
                "themes": themes,
                "emotional_tone": "neutral",
                "reflection": f'You wrote: "{answer[:300]}". This reply stays with those words.',
                "follow_up_question": "What happened right after that?",
            }
        )
