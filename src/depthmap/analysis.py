import logging

from pydantic import ValidationError

from depthmap.codebook import Codebook
from depthmap.models import Analysis, AnalysisOutput
from depthmap.prompts.analysis import ANALYSIS_PROMPT_VERSION, build_system_prompt
from depthmap.providers.base import LLMProvider
from depthmap.validator import Rule, Violation, find_violations

logger = logging.getLogger(__name__)


class AnalysisParseError(Exception):
    def __init__(self, raw: str, problems: list[str]):
        super().__init__("; ".join(problems))
        self.raw = raw
        self.problems = problems


class AnalysisValidationError(Exception):
    def __init__(self, raw: str, violations: list[Violation]):
        super().__init__("; ".join(f"{v.rule_id}: {v.message}" for v in violations))
        self.raw = raw
        self.violations = violations


def problem_text(problem) -> str:
    # a reply that is not JSON at all has a message but no location
    where = ".".join(str(part) for part in problem["loc"])
    return f"{where}: {problem['msg']}" if where else problem["msg"]


def analyze(
    question: str,
    response: str,
    provider: LLMProvider,
    codebook: Codebook,
    rules: list[Rule],
    client_emotion: str | None = None,
) -> Analysis:
    """Get an analysis of one answer, asking a second time if the first reply is not usable."""
    system = build_system_prompt(codebook)
    user = f"Question: {question}\n\nAnswer: {response}"
    known = set(codebook.active_ids())
    for attempt in (1, 2):
        raw = provider.complete_json(system, user, AnalysisOutput)
        try:
            output = AnalysisOutput.model_validate_json(raw)
        except ValidationError as invalid:
            problems = [problem_text(problem) for problem in invalid.errors()]
        else:
            # the schema cannot list the codebook ids, so a made-up id is caught here
            problems = [f"themes: unknown id {t}" for t in output.themes if t not in known]
        if problems:
            logger.warning("reply %d of 2 failed validation: %s", attempt, "; ".join(problems))
            error = AnalysisParseError(raw, problems)
            continue

        violations = find_violations(output, rules, context=response)
        if violations:
            error = AnalysisValidationError(raw, violations)
            logger.warning("reply %d of 2 was rejected: %s", attempt, error)
            reasons = "; ".join(v.message for v in violations)
            # the note goes first so the answer stays the last thing in the prompt
            user = f"Your last reply was rejected. This time: {reasons}.\n\n{user}"
            continue

        # client_emotion is the client's own word and never comes from the model
        return Analysis(
            **output.model_dump(),
            client_emotion=client_emotion,
            prompt_version=ANALYSIS_PROMPT_VERSION,
            codebook_version=codebook.version,
        )
    raise error
