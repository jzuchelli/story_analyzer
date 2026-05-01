import asyncio
import importlib.util
import os
from functools import lru_cache
from typing import Any

from models import (
    StoryClassification,
    StoryValidationRequest,
    ValidationCheck,
    ValidationResult,
)


ZERO_SHOT_LABELS = [
    "clear requirement",
    "testable acceptance criteria",
    "contains business value",
    "too vague",
    "too large",
    "ready for work",
]

DEFAULT_MODEL = "facebook/bart-large-mnli"


class HuggingFaceUnavailableError(RuntimeError):
    pass


class HuggingFaceClassificationError(RuntimeError):
    pass


def _installed_ml_backends() -> list[str]:
    return [
        backend
        for backend in ("torch", "tensorflow", "flax")
        if importlib.util.find_spec(backend) is not None
    ]


def get_huggingface_status() -> dict[str, Any]:
    model_name = os.getenv("HUGGINGFACE_ZERO_SHOT_MODEL", DEFAULT_MODEL)
    backends = _installed_ml_backends()
    return {
        "available": bool(backends),
        "model": model_name,
        "labels": ZERO_SHOT_LABELS,
        "backends": backends,
    }


def _require_ml_backend() -> None:
    if _installed_ml_backends():
        return

    raise HuggingFaceUnavailableError(
        "Hugging Face zero-shot classification requires an ML backend. "
        "Install the project dependencies with torch included."
    )


def _build_story_context(request: StoryValidationRequest) -> str:
    acceptance_criteria = "\n".join(
        f"- {criterion}" for criterion in request.acceptanceCriteria
    )
    dependencies = "\n".join(f"- {dependency}" for dependency in request.dependencies)

    return "\n".join(
        [
            f"Title: {request.title}",
            f"Story: {request.story}",
            "Acceptance criteria:",
            acceptance_criteria or "- none",
            f"Priority: {request.priority or 'none'}",
            f"Estimate: {request.estimate or 'none'}",
            "Dependencies:",
            dependencies or "- none",
        ]
    )


@lru_cache(maxsize=1)
def _get_zero_shot_classifier() -> Any:
    _require_ml_backend()

    try:
        from transformers import pipeline
    except ImportError as exc:
        raise HuggingFaceUnavailableError(
            "Install transformers and a supported ML backend to enable "
            "Hugging Face zero-shot classification."
        ) from exc

    model_name = os.getenv("HUGGINGFACE_ZERO_SHOT_MODEL", DEFAULT_MODEL)
    device = int(os.getenv("HUGGINGFACE_ZERO_SHOT_DEVICE", "-1"))
    return pipeline("zero-shot-classification", model=model_name, device=device)


def classify_story(request: StoryValidationRequest) -> StoryClassification:
    model_name = os.getenv("HUGGINGFACE_ZERO_SHOT_MODEL", DEFAULT_MODEL)
    try:
        classifier = _get_zero_shot_classifier()
        result = classifier(
            _build_story_context(request),
            candidate_labels=ZERO_SHOT_LABELS,
            multi_label=False,
        )
    except HuggingFaceUnavailableError:
        raise
    except Exception as exc:
        raise HuggingFaceClassificationError(
            "Hugging Face zero-shot classification failed."
        ) from exc

    labels = result["labels"]
    scores = result["scores"]
    score_by_label = {
        label: round(float(score), 4)
        for label, score in zip(labels, scores)
    }

    return StoryClassification(
        label=labels[0],
        confidence=round(float(scores[0]), 4),
        scores=score_by_label,
        model=model_name,
    )


def _suggestions_for_classification(
    classification: StoryClassification,
) -> list[str]:
    if classification.label == "too vague":
        return [
            "Clarify the user, desired capability, and outcome before pulling this story into work."
        ]
    if classification.label == "too large":
        return [
            "Split this story into smaller vertical slices that can be completed independently."
        ]
    if classification.label == "testable acceptance criteria":
        return []
    if classification.label == "contains business value":
        return []
    if classification.label == "clear requirement":
        return []
    if classification.label == "ready for work":
        return []
    return []


async def classify_story_async(
    request: StoryValidationRequest,
) -> StoryClassification:
    return await asyncio.to_thread(classify_story, request)


async def validate_with_ai(
    request: StoryValidationRequest,
    classification: StoryClassification | None = None,
) -> ValidationResult:
    if classification is None:
        return ValidationResult(
            checks=[],
            suggestions=[],
        )

    negative_labels = {"too vague", "too large"}
    return ValidationResult(
        checks=[
            ValidationCheck(
                name="classifiedByHuggingFace",
                passed=True,
                message=(
                    "Story was classified by Hugging Face zero-shot "
                    f"model {classification.model}."
                ),
            ),
            ValidationCheck(
                name="classificationSupportsReadiness",
                passed=classification.label not in negative_labels,
                message=(
                    "Hugging Face classification does not identify the story "
                    "as too vague or too large."
                ),
            ),
        ],
        suggestions=_suggestions_for_classification(classification),
    )
