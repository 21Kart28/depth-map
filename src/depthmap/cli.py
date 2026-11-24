import argparse

from anthropic import Anthropic
from pydantic import ValidationError

from depthmap.models import Analysis
from depthmap.questions import load_bank

MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = """\
You are a careful, non-clinical listener. The user has answered a reflective question.
Analyze the answer:

themes: 1 to 5 short noun phrases in lowercase, each based on something the user actually wrote
emotional_tone: one short phrase in lowercase
reflection: 2 to 5 sentences that reflect the answer back, quoting or paraphrasing the user
follow_up_question: one open question that goes one level deeper, ending with "?"

Stay with what the user said. Do not add your own reading of what it means or what is behind it.
Ask one thing in the follow-up question, not two joined by "and".
No diagnosis, no advice, no platitudes, no psychology jargon."""


def main():
    bank = load_bank()

    parser = argparse.ArgumentParser(prog="depthmap")
    parser.add_argument("--question-id", choices=[q.id for q in bank.questions])
    args = parser.parse_args()

    counts = {q.id: 0 for q in bank.questions}
    question = bank.get(args.question_id) if args.question_id else bank.next(counts)

    # reads ANTHROPIC_API_KEY from the environment
    client = Anthropic()

    print("Type q to quit.")
    while True:
        print()
        print(question.text)
        response = input("> ")
        if response.strip().lower() == "q":
            break

        content = f"Question: {question.text}\n\nAnswer: {response}"
        try:
            message = client.messages.parse(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}],
                output_format=Analysis,
            )
        except ValidationError as error:
            print("\nthe analysis didn't pass validation:")
            for problem in error.errors():
                field = ".".join(str(part) for part in problem["loc"])
                print(f"  {field}: {problem['msg']}")
            continue
        analysis = message.parsed_output

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
