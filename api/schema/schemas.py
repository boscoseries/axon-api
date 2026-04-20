from pydantic import BaseModel
from typing import Literal
from enum import Enum


class IssueSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class IssueType(str, Enum):
    grammar = "grammar"
    completeness = "completeness"


class Issue(BaseModel):
    type: IssueType
    severity: IssueSeverity
    detail: str
    location: str  # e.g. "Paragraph 2", "Section: Introduction", "Line 14"


class ReviewResponse(BaseModel):
    score: int                  # 0–100 overall quality score
    summary: str                # one-paragraph human-readable summary
    issues: list[Issue]
    model_used: str
    document_name: str
    word_count: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model: str
    environment: str


class ModelsResponse(BaseModel):
    provider: str
    models: list[str]