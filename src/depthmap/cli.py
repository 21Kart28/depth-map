import argparse
import logging

from depthmap.analysis import AnalysisParseError, AnalysisValidationError, analyze
from depthmap.codebook import load_codebook
from depthmap.config import Settings
from depthmap.models import DEFAULT_CLIENT_ID, Entry, QuestionV2
from depthmap.providers import ProviderError, get_provider
from depthmap.questions import load_bank
from depthmap.store import get_repository
from depthmap.validator import load_rules


def main():
    settings = Settings()
    bank = load_bank(settings.question_bank)
    codebook = load_codebook()
    rules = load_rules()

    parser = argparse.ArgumentParser(prog="depthmap")
    parser.add_argument("--question-id", choices=[q.id for q in bank.questions])
    args = parser.parse_args()

    logging.basicConfig(level=settings.log_level)
    provider = get_provider(settings)

    repo = get_repository(settings)
    history = repo.question_history(DEFAULT_CLIENT_ID)
    question = bank.next(history, pinned_id=args.question_id)

    print(f"Provider: {provider.name}")
    print(f"Entries so far: {len(history)}")
    print("Type q to quit.")
    while True:
        print()
        if isinstance(question, QuestionV2):
            print(question.framing)
        print(question.text)
        response = input("> ").strip()
        if response.lower() == "q":
            break
        # the API refuses a blank answer, so here the question is asked again
        if not response:
            continue

        try:
            analysis = analyze(question.text, response, provider, codebook, rules)
        except AnalysisParseError as error:
            print("\nthe analysis didn't pass validation:")
            for problem in error.problems:
                print(f"  {problem}")
            continue
        except AnalysisValidationError as error:
            print("\nthe analysis was rejected:")
            for violation in error.violations:
                print(f"  {violation.rule_id}: {violation.message}")
            continue
        except ProviderError as error:
            print(f"\n{error}")
            continue

        print()
        print("Themes:")
        for theme in analysis.themes:
            print(f"  - {theme}: {codebook.get(theme).label}")
        print(f"Tone: {', '.join(analysis.tone.labels)}")
        print()
        print(analysis.reflection)
        print()
        print(analysis.follow_up_question)

        repo.add(
            Entry(
                question_id=question.id,
                question_text=question.text,
                response=response,
                analysis=analysis,
                prompt_version=analysis.prompt_version,
                codebook_version=analysis.codebook_version,
                provider=provider.name,
            )
        )
        question = bank.next(repo.question_history(DEFAULT_CLIENT_ID))
