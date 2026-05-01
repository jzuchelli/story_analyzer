import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from models import StoryValidationRequest, StoryValidationResponse, ValidationResult
from scoring.readiness_score import calculate_readiness_score, get_readiness_status
from validators.ai_validator import (
    HuggingFaceClassificationError,
    HuggingFaceUnavailableError,
    classify_story_async,
    get_huggingface_status,
    validate_with_ai,
)
from validators.rule_validator import validate_rules

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/huggingface/status")
async def huggingface_status():
    return get_huggingface_status()


@app.post("/validate-story", response_model=StoryValidationResponse)
async def validate_story(request: StoryValidationRequest):
    rule_validation = validate_rules(request)
    try:
        classification = await classify_story_async(request)
    except HuggingFaceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HuggingFaceClassificationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    ai_validation = await validate_with_ai(request, classification)
    checks = [*rule_validation.checks, *ai_validation.checks]
    score = calculate_readiness_score(checks)

    return StoryValidationResponse(
        readyForWork=score == 100,
        score=score,
        status=get_readiness_status(score),
        checks=checks,
        suggestions=[*rule_validation.suggestions, *ai_validation.suggestions],
        classification=classification,
    )


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    return value


def _stream_event(event_type: str, payload: dict[str, Any]) -> str:
    return json.dumps(_dump({"type": event_type, **payload})) + "\n"


async def _run_rule_validation(request: StoryValidationRequest) -> ValidationResult:
    return await asyncio.to_thread(validate_rules, request)


async def _run_ai_validation(
    request: StoryValidationRequest,
) -> tuple[Any, ValidationResult]:
    classification = await classify_story_async(request)
    ai_validation = await validate_with_ai(request, classification)
    return classification, ai_validation


@app.post("/validate-story/stream")
async def validate_story_stream(request: StoryValidationRequest):
    async def stream_results():
        rule_task = asyncio.create_task(_run_rule_validation(request))
        ai_task = asyncio.create_task(_run_ai_validation(request))
        pending = {rule_task, ai_task}

        rule_validation: ValidationResult | None = None
        ai_validation: ValidationResult | None = None
        classification = None

        try:
            while pending:
                done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in done:
                    if task is rule_task:
                        rule_validation = task.result()
                        yield _stream_event(
                            "rules_complete",
                            {
                                "checks": _dump(rule_validation.checks),
                                "suggestions": rule_validation.suggestions,
                            },
                        )
                        continue

                    try:
                        classification, ai_validation = task.result()
                    except HuggingFaceUnavailableError as exc:
                        yield _stream_event("error", {"message": str(exc)})
                        return
                    except HuggingFaceClassificationError as exc:
                        yield _stream_event("error", {"message": str(exc)})
                        return

                    yield _stream_event(
                        "ai_complete",
                        {
                            "checks": _dump(ai_validation.checks),
                            "suggestions": ai_validation.suggestions,
                            "classification": _dump(classification),
                        },
                    )

            if rule_validation is None or ai_validation is None:
                yield _stream_event(
                    "error",
                    {"message": "Validation did not complete."},
                )
                return

            checks = [*rule_validation.checks, *ai_validation.checks]
            score = calculate_readiness_score(checks)
            response = StoryValidationResponse(
                readyForWork=score == 100,
                score=score,
                status=get_readiness_status(score),
                checks=checks,
                suggestions=[
                    *rule_validation.suggestions,
                    *ai_validation.suggestions,
                ],
                classification=classification,
            )
            yield _stream_event("final", {"result": _dump(response)})
        except asyncio.CancelledError:
            raise
        finally:
            for task in pending:
                task.cancel()

    return StreamingResponse(
        stream_results(),
        media_type="application/x-ndjson",
    )


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
