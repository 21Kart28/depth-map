from anthropic import Anthropic
from pydantic import BaseModel

MODEL = "claude-haiku-5-5"

QUESTION = (
    "What is something you keep telling yourself you'll deal with later? "
    "What happens when you imagine dealing with it now?"
)

SYSTEM_PROMPT = """\
You are a careful, non-clinical listener. The user has answered a reflective question.
Analyze the answer:

themes: 1 to 5 short noun phrases, each based on something the user actually wrote
emotional_tone: one short phrase
reflection: 2 to 5 sentences that reflect the answer back, quoting or paraphrasing the user
follow_up_question: one open question that goes one level deeper, ending with "?"

No diagnosis, no advice, no platitudes, no psychology jargon."""


class Analysis(BaseModel):
    themes: list[str]
    emotional_tone: str
    reflection: str
    follow_up_question: str


def main():
    # reads ANTHROPIC_API_KEY from the environment
    client = Anthropic()

    print(QUESTION)
    response = input("> ")

    message = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Question: {QUESTION}\n\nAnswer: {response}"}],
        output_format=Analysis,
    )
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


if __name__ == "__main__":
    main()
