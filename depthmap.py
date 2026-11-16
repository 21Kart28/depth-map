from typing import Annotated

from anthropic import Anthropic
from pydantic import BaseModel, Field, StringConstraints, ValidationError, field_validator

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


Theme = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]


class Analysis(BaseModel):
    # the API only enforces the field names and types; these limits reach the model as hints
    # and are checked here when the reply comes back
    themes: list[Theme] = Field(min_length=1, max_length=5)
    emotional_tone: str = Field(min_length=2, max_length=60)
    reflection: str = Field(min_length=40, max_length=1200)
    follow_up_question: str = Field(min_length=10, max_length=300)

    @field_validator("follow_up_question")
    @classmethod
    def ends_with_question_mark(cls, value: str) -> str:
        if not value.rstrip().endswith("?"):
            raise ValueError("must end with a question mark")
        return value


def main():
    # reads ANTHROPIC_API_KEY from the environment
    client = Anthropic()

    print(QUESTION)
    response = input("> ")

    try:
        message = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Question: {QUESTION}\n\nAnswer: {response}"}],
            output_format=Analysis,
        )
    except ValidationError as error:
        print("\nthe analysis didn't pass validation:")
        for problem in error.errors():
            field = ".".join(str(part) for part in problem["loc"])
            print(f"  {field}: {problem['msg']}")
        return
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
