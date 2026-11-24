from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

Theme = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]


class Question(BaseModel):
    """One question from the bank."""

    id: str
    category: str
    text: str


class Analysis(BaseModel):
    """The model's reading of one answer."""

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
