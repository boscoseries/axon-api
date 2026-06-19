from pydantic import BaseModel, Field
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
    invalid_variable: str = Field(alias="invalid variable")
    reason: str
    valid_variable: str = Field(alias="valid variable")


class ReviewResponse(BaseModel):
    has_issues: bool 
    issues: list[Issue]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model: str
    environment: str


class ModelsResponse(BaseModel):
    providers: dict[str, list[str]]


class ActiveModelResponse(BaseModel):
    model: str
    provider: str


class MedicalQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class MedicalQueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks_used: int