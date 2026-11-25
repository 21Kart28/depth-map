import logging

from pydantic import ValidationError

from depthmap.models import Analysis
from depthmap.prompts.analysis import SYSTEM_PROMPT
from depthmap.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class AnalysisParseError(Exception):
    def __init__(self, raw: str, problems: list[str]):
        super().__init__("; ".join(problems))
        self.raw = raw
        self.problems = problems


def analyze(question: str, response: str, provider: LLMProvider) -> Analysis:
    """Get an analysis of one answer, asking a second time if the first reply is not valid."""
    user = f"Question: {question}\n\nAnswer: {response}"
    for attempt in (1, 2):
        raw = provider.complete_json(SYSTEM_PROMPT, user, Analysis)
        try:
            return Analysis.model_validate_json(raw)
        except ValidationError as error:
            problems = [
                f"{'.'.join(str(part) for part in problem['loc'])}: {problem['msg']}"
                for problem in error.errors()
            ]
            logger.warning("reply %d of 2 failed validation: %s", attempt, "; ".join(problems))
    raise AnalysisParseError(raw, problems)
