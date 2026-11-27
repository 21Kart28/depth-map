import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from depthmap import __version__
from depthmap.analysis import AnalysisParseError, AnalysisValidationError, analyze
from depthmap.codebook import load_codebook
from depthmap.config import Settings
from depthmap.docs import add_docs_page
from depthmap.models import (
    DEFAULT_CLIENT_ID,
    CreateEntryRequest,
    Entry,
    ErrorResponse,
    HealthResponse,
    Question,
    QuestionV2,
)
from depthmap.providers import LLMProvider, ProviderError, get_provider
from depthmap.questions import load_bank
from depthmap.store import Repository, get_repository
from depthmap.validator import load_rules

logger = logging.getLogger(__name__)

DESCRIPTION = (
    "Depth Map asks one reflective question at a time and stores each answer with an analysis "
    "of it: themes picked from a fixed codebook, tone, a short reflection and a follow-up "
    "question. Entries are kept in a SQLite file."
)

NOT_FOUND = {404: {"model": ErrorResponse}}
ANALYSIS_FAILED = {502: {"model": ErrorResponse}}


def error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse({"error": error, "detail": detail}, status_code=status_code)


def create_app(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
    repo: Repository | None = None,
) -> FastAPI:
    """Build the API. Tests pass in a fake provider and a fresh repository."""
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level)
    if provider is None:
        provider = get_provider(settings)
    if repo is None:
        repo = get_repository(settings)
    bank = load_bank(settings.question_bank)
    codebook = load_codebook()
    rules = load_rules()

    app = FastAPI(
        title="Depth Map API", version=__version__, description=DESCRIPTION, docs_url=None
    )
    add_docs_page(app)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException):
        name = HTTPStatus(error.status_code).phrase.lower().replace(" ", "_")
        return error_response(error.status_code, name, error.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        problems = [
            f"{'.'.join(str(part) for part in problem['loc'])}: {problem['msg']}"
            for problem in error.errors()
        ]
        return error_response(422, "validation_error", "; ".join(problems))

    @app.exception_handler(ProviderError)
    async def provider_error(request: Request, error: ProviderError):
        logger.error("%s", error)
        return error_response(502, "provider_error", str(error))

    @app.exception_handler(AnalysisParseError)
    async def analysis_parse_error(request: Request, error: AnalysisParseError):
        logger.error("analysis failed validation twice: %s", error)
        return error_response(502, "analysis_parse_error", str(error))

    @app.exception_handler(AnalysisValidationError)
    async def analysis_validation_error(request: Request, error: AnalysisValidationError):
        logger.error("analysis was rejected twice: %s", error)
        return error_response(502, "analysis_validation_error", str(error))

    # the routes are plain def, not async def, so FastAPI runs them in a worker thread
    # and the blocking model call does not hold up other requests

    @app.get("/health")
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__, provider=provider.name)

    @app.get("/questions")
    def list_questions() -> list[Question] | list[QuestionV2]:
        return bank.questions

    # declared before /questions/{question_id}, or "next" would be read as an id
    @app.get("/questions/next")
    def next_question(client_id: str = DEFAULT_CLIENT_ID) -> Question | QuestionV2:
        return bank.next(repo.question_history(client_id))

    @app.get("/questions/{question_id}", responses=NOT_FOUND)
    def get_question(question_id: str) -> Question | QuestionV2:
        question = bank.get(question_id)
        if question is None:
            raise HTTPException(404, "question not found")
        return question

    @app.post("/entries", status_code=201, responses=NOT_FOUND | ANALYSIS_FAILED)
    def create_entry(body: CreateEntryRequest) -> Entry:
        question = bank.get(body.question_id)
        if question is None:
            raise HTTPException(404, "question not found")

        analysis = analyze(
            question.text, body.response, provider, codebook, rules, body.client_emotion
        )
        # nothing is stored unless the analysis succeeded
        entry = repo.add(
            Entry(
                client_id=body.client_id,
                question_id=question.id,
                question_text=question.text,
                response=body.response,
                analysis=analysis,
                prompt_version=analysis.prompt_version,
                codebook_version=analysis.codebook_version,
                provider=provider.name,
            )
        )
        logger.info("stored entry %s for question %s", entry.id, question.id)
        return entry

    @app.get("/entries")
    def list_entries(limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[Entry]:
        return repo.list(limit)

    @app.get("/entries/{entry_id}", responses=NOT_FOUND)
    def get_entry(entry_id: str) -> Entry:
        entry = repo.get(entry_id)
        if entry is None:
            raise HTTPException(404, "entry not found")
        return entry

    return app


app = create_app()
