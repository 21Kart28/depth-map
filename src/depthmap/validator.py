"""Checks a model reply for wording the schema cannot catch, using data/banned_terms.json."""

import json
import logging
import re
from dataclasses import dataclass
from importlib import resources

from depthmap.models import AnalysisOutput

logger = logging.getLogger(__name__)

CATEGORIES = {"advice", "diagnosis", "reassurance", "praise", "date"}


@dataclass
class Rule:
    id: str
    category: str
    patterns: list[re.Pattern]
    message: str
    allowed_from_context: bool = False


@dataclass
class Violation:
    rule_id: str
    category: str
    message: str


def parse_rules(data: dict) -> list[Rule]:
    """Check the shape of a rules file and compile its patterns, naming the rule that is wrong."""
    rules = []
    for item in data["rules"]:
        rule_id = item["id"]
        if item.get("category") not in CATEGORIES:
            raise ValueError(f"rule {rule_id}: unknown category {item.get('category')!r}")
        patterns = []
        for pattern in item["patterns"]:
            try:
                patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as error:
                raise ValueError(f"rule {rule_id}: bad pattern {pattern!r}") from error
        rules.append(
            Rule(
                id=rule_id,
                category=item["category"],
                patterns=patterns,
                message=item["message"],
                allowed_from_context=item.get("allowed_from_context", False),
            )
        )
    return rules


def load_rules() -> list[Rule]:
    path = resources.files("depthmap") / "data" / "banned_terms.json"
    return parse_rules(json.loads(path.read_text(encoding="utf-8")))


def find_violations(output: AnalysisOutput, rules: list[Rule], context: str) -> list[Violation]:
    """The rules a reply breaks, at most one violation per rule. context is the client's text."""
    # change_talk and sustain_talk are left out: they are quotes of the client, not model wording
    text = "\n".join(
        [
            output.reflection,
            output.follow_up_question,
            *output.candidate_themes,
            *output.tone.labels,
        ]
    )
    context = context.lower()
    violations = []
    for rule in rules:
        for pattern in rule.patterns:
            match = pattern.search(text)
            if match is None:
                continue
            if rule.allowed_from_context and match.group().lower() in context:
                continue
            # the rule id is logged, never the matched words, which can be the client's own
            logger.info("rule %s (%s) matched", rule.id, rule.category)
            violations.append(Violation(rule.id, rule.category, rule.message))
            break
    return violations
