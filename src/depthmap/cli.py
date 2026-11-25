import argparse
import logging

from depthmap.analysis import AnalysisParseError, analyze
from depthmap.config import Settings
from depthmap.providers import ProviderError, get_provider
from depthmap.questions import load_bank


def main():
    bank = load_bank()

    parser = argparse.ArgumentParser(prog="depthmap")
    parser.add_argument("--question-id", choices=[q.id for q in bank.questions])
    args = parser.parse_args()

    settings = Settings()
    logging.basicConfig(level=settings.log_level)
    provider = get_provider(settings)

    counts = {q.id: 0 for q in bank.questions}
    question = bank.get(args.question_id) if args.question_id else bank.next(counts)

    print(f"Provider: {provider.name}")
    print("Type q to quit.")
    while True:
        print()
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

        counts[question.id] += 1
        question = bank.next(counts)
