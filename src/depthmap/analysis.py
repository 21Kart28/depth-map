import logging

from pydantic import ValidationError

from depthmap.codebook import Codebook
from depthmap.models import Analysis, AnalysisOutput
from depthmap.prompts.analysis import ANALYSIS_PROMPT_VERSION, build_system_prompt
from depthmap.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class AnalysisParseError(Exception):
    def __init__(self, raw: str, problems: list[str]):
        super().__init__("; ".join(problems))
        self.raw = raw
        self.problems = problems


def analyze(
    question: str,
    response: str,
    provider: LLMProvider,
    codebook: Codebook,
    client_emotion: str | None = None,
) -> Analysis:
    """Get an analysis of one answer, asking a second time if the first reply is not valid."""
    system = build_system_prompt(codebook)
    user = f"Question: {question}\n\nAnswer: {response}"
    known = set(codebook.active_ids())
    for attempt in (1, 2):
        raw = provider.complete_json(system, user, AnalysisOutput)
        try:
            output = AnalysisOutput.model_validate_json(raw)
        except ValidationError as error:
            problems = [
                f"{'.'.join(str(part) for part in problem['loc'])}: {problem['msg']}"
                for problem in error.errors()
            ]
        else:
            # the schema cannot list the codebook ids, so a made-up id is caught here
            problems = [f"themes: unknown id {t}" for t in output.themes if t not in known]
            if not problems:
                # client_emotion is the client's own word and never comes from the model
                return Analysis(
                    **output.model_dump(),
                    client_emotion=client_emotion,
                    prompt_version=ANALYSIS_PROMPT_VERSION,
                    codebook_version=codebook.version,
                )
        logger.warning("reply %d of 2 failed validation: %s", attempt, "; ".join(problems))
    raise AnalysisParseError(raw, problems)
