from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, StringConstraints, field_validator

DEFAULT_CLIENT_ID = "local"

Theme = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]


class Question(BaseModel):
    """One question from the bank."""

    id: str
    category: str
    text: str


class QuestionV2(BaseModel):
    """One question from the v2 bank: a framing sentence, then the question."""

    id: str
    domain: str
    mode: str
    framing: str
    text: str
    clinician_gated: bool
    schema_hooks: list[str]


class Code(BaseModel):
    """One theme from the codebook."""

    id: str
    group: str
    label: str
    definition: str
    example: str
    counter_example: str


class ThemeConfidence(BaseModel):
    """How sure the model is about one of the themes it picked."""

    theme: str
    confidence: Literal["low", "med", "high"]


class Tone(BaseModel):
    """How the answer reads: valence from -1 to 1, arousal from 0 to 1, a few labels."""

    valence: float = Field(ge=-1, le=1)
    arousal: float = Field(ge=0, le=1)
    labels: list[Theme] = Field(max_length=3)


class RelationalEpisode(BaseModel):
    """One interaction: what the client wanted, what the other person did, what the client did."""

    wish: str
    response_of_other: str
    response_of_self: str


class AnalysisOutput(BaseModel):
    """The part of an analysis the model writes."""

    # the API only enforces the field names and types; these limits reach the model as hints
    # and are checked here when the reply comes back
    themes: list[str] = Field(min_length=1, max_length=4)
    candidate_themes: list[Theme] = Field(max_length=2)
    # a list, not a map from id to level: the API's schema format has no free-form keys
    theme_confidence: list[ThemeConfidence]
    tone: Tone
    relational_episode: RelationalEpisode | None
    change_talk: str | None = Field(max_length=300)
    sustain_talk: str | None = Field(max_length=300)
    reflection: str = Field(min_length=40, max_length=1200)
    follow_up_question: str = Field(min_length=10, max_length=300)

    @field_validator("follow_up_question")
    @classmethod
    def ends_with_question_mark(cls, value: str) -> str:
        if not value.rstrip().endswith("?"):
            raise ValueError("must end with a question mark")
        return value

    @field_validator("themes")
    @classmethod
    def no_repeated_theme(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("the same id twice")
        return value

    @field_validator("theme_confidence")
    @classmethod
    def one_confidence_per_theme(cls, value: list[ThemeConfidence], info) -> list[ThemeConfidence]:
        if sorted(item.theme for item in value) != sorted(info.data.get("themes", [])):
            raise ValueError("needs one item for each theme")
        return value


class Analysis(AnalysisOutput):
    """One answer's analysis as stored: the model's part plus what the app adds."""

    client_emotion: str | None = None
    prompt_version: str
    codebook_version: str


class Entry(BaseModel):
    """One answer to one question, stored with its analysis."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    # every entry carries a client id from the start so retrieval can be scoped per client later
    client_id: str = DEFAULT_CLIENT_ID
    question_id: str
    question_text: str
    response: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    analysis: Analysis
    prompt_version: str
    codebook_version: str
    provider: str


class CreateEntryRequest(BaseModel):
    """Body of POST /entries."""

    question_id: str
    response: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)
    ]
    client_emotion: str | None = Field(default=None, max_length=60)
    client_id: str = Field(default=DEFAULT_CLIENT_ID, min_length=1, max_length=64)


class HealthResponse(BaseModel):
    """Body of GET /health."""

    status: str
    version: str
    provider: str


class ErrorResponse(BaseModel):
    """Body of every error reply."""

    error: str
    detail: str
