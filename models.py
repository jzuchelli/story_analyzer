from pydantic import BaseModel, Field


class StoryValidationRequest(BaseModel):
    title: str = ""
    story: str = ""
    acceptanceCriteria: list[str] = Field(default_factory=list)
    priority: str = ""
    estimate: str = ""
    dependencies: list[str] = Field(default_factory=list)


class ValidationCheck(BaseModel):
    name: str
    passed: bool
    message: str


class ValidationResult(BaseModel):
    checks: list[ValidationCheck]
    suggestions: list[str] = Field(default_factory=list)


class StoryClassification(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    scores: dict[str, float] = Field(default_factory=dict)
    model: str


class StoryValidationResponse(BaseModel):
    readyForWork: bool
    score: int = Field(ge=0, le=100)
    status: str
    checks: list[ValidationCheck]
    suggestions: list[str]
    classification: StoryClassification | None = None
