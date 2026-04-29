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
    type: str
    found: str
    suggested: str
    reason: str


class ReviewResponse(BaseModel):
    has_issues: bool 
    issues: list[Issue]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model: str
    environment: str


class ModelsResponse(BaseModel):
    provider: str
    models: list[str]