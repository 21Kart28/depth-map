import argparse
import logging

from depthmap.analysis import AnalysisParseError, analyze
from depthmap.config import Settings
from depthmap.models import DEFAULT_CLIENT_ID, Entry, QuestionV2
from depthmap.prompts.analysis import ANALYSIS_PROMPT_VERSION
from depthmap.providers import ProviderError, get_provider
from depthmap.questions import load_bank
from depthmap.store import get_repository


def main():
    settings = Settings()
    bank = load_bank(settings.question_bank)

    parser = argparse.ArgumentParser(prog="depthmap")
    parser.add_argument("--question-id", choices=[q.id for q in bank.questions])
    args = parser.parse_args()

    logging.basicConfig(level=settings.log_level)
    provider = get_provider(settings)

    repo = get_repository(settings)
    counts = repo.count_by_question(DEFAULT_CLIENT_ID)
    question = bank.get(args.question_id) if args.question_id else bank.next(counts)

    print(f"Provider: {provider.name}")
    print(f"Entries so far: {sum(counts.values())}")
    print("Type q to quit.")
    while True:
        print()
        if isinstance(question, QuestionV2):
            print(question.framing)
        print(question.text)
        response = input("> ")
        if response.strip().lower() == "q":
            break

        try:
            analysis = analyze(question.text, response, provider)
        except AnalysisParseError as error:
            print("\nthe analysis didn't pass validation:")
            for problem in error.problems:
                print(f"  {problem}")
            continue
        except ProviderError as error:
            print(f"\n{error}")
            continue

        print()
        print("Themes:")
        for theme in analysis.themes:
            print(f"  - {theme}")
        print(f"Tone: {analysis.emotional_tone}")
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
                prompt_version=ANALYSIS_PROMPT_VERSION,
                provider=provider.name,
            )
        )
        question = bank.next(repo.count_by_question(DEFAULT_CLIENT_ID))
