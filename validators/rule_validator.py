from models import StoryValidationRequest, ValidationCheck, ValidationResult


MAX_STORY_WORD_COUNT = 250
MIN_CLEAR_STORY_WORD_COUNT = 8


def _has_user_story_format(story: str) -> bool:
    normalized_story = story.lower()
    return all(
        phrase in normalized_story
        for phrase in ("as a", "i want", "so that")
    )


def _has_business_value(story: str) -> bool:
    normalized_story = story.lower()
    value_markers = (
        "so that",
        "in order to",
        "benefit",
        "value",
        "because",
    )
    return any(marker in normalized_story for marker in value_markers)


def _criteria_are_testable(acceptance_criteria: list[str]) -> bool:
    if not acceptance_criteria:
        return False

    testable_markers = (
        "given",
        "when",
        "then",
        "should",
        "must",
        "can",
        "verify",
        "display",
        "return",
        "show",
        "prevent",
        "allow",
    )

    return all(
        any(marker in criterion.lower() for marker in testable_markers)
        for criterion in acceptance_criteria
    )


def _has_dependencies_listed_or_marked_none(dependencies: list[str]) -> bool:
    if not dependencies:
        return False

    return all(dependency.strip() for dependency in dependencies)


def _story_is_clear(story: str) -> bool:
    words = story.split()
    return len(words) >= MIN_CLEAR_STORY_WORD_COUNT and _has_user_story_format(story)


def validate_rules(request: StoryValidationRequest) -> ValidationResult:
    story_text = request.story.strip()
    words = story_text.split()

    checks = [
        ValidationCheck(
            name="hasTitle",
            passed=bool(request.title.strip()),
            message="Has title.",
        ),
        ValidationCheck(
            name="hasUserStoryFormat",
            passed=_has_user_story_format(story_text),
            message='Has user story format: "As a..., I want..., so that...".',
        ),
        ValidationCheck(
            name="hasBusinessValue",
            passed=_has_business_value(story_text),
            message="Has business value.",
        ),
        ValidationCheck(
            name="hasAcceptanceCriteria",
            passed=bool(request.acceptanceCriteria),
            message="Has acceptance criteria.",
        ),
        ValidationCheck(
            name="acceptanceCriteriaAreTestable",
            passed=_criteria_are_testable(request.acceptanceCriteria),
            message="Acceptance criteria are testable.",
        ),
        ValidationCheck(
            name="hasPriority",
            passed=bool(request.priority.strip()),
            message="Has priority.",
        ),
        ValidationCheck(
            name="hasEstimate",
            passed=bool(request.estimate.strip()),
            message="Has estimate.",
        ),
        ValidationCheck(
            name="hasDependencies",
            passed=_has_dependencies_listed_or_marked_none(request.dependencies),
            message='Has dependencies listed or marked "none".',
        ),
        ValidationCheck(
            name="storyIsClear",
            passed=_story_is_clear(story_text),
            message="Story is clear.",
        ),
        ValidationCheck(
            name="storyIsNotTooLarge",
            passed=bool(words) and len(words) <= MAX_STORY_WORD_COUNT,
            message=f"Story is not too large, with {MAX_STORY_WORD_COUNT} words or fewer.",
        ),
    ]

    suggestions = [check.message for check in checks if not check.passed]

    return ValidationResult(
        checks=checks,
        suggestions=suggestions,
    )
