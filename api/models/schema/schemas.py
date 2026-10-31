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
    query: str = Field(
        ...,
        description="Free-text medical question to answer using the RAG knowledge base.",
        examples=["What are the available treatment options and management strategies for chronic kidney disease?"],
    )
    top_k: int = 5


class MedicalQueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks_used: int

class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to summarise, e.g. a lesson transcript.")
    title: str | None = Field(None, description="Optional title, to give the model context.")
    max_points: int | None = Field(None, ge=1, le=50, description="Most key points to return; leave out for all of them.")


class SummarizeResponse(BaseModel):
    summary: str
    key_points: list[str]


class AskTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    material: str = Field(..., min_length=1, description="The only text the answer may come from: a lesson's transcript and/or summary.")
    title: str | None = None
    history: list[AskTurn] = Field(default_factory=list, description="Earlier questions and answers, oldest first.")


class AskSource(BaseModel):
    text: str
    start_ms: int | None = None


class AskResponse(BaseModel):
    found: bool
    answer: str
    sources: list[AskSource] = []


class FlashcardsRequest(BaseModel):
    material: str = Field(..., min_length=1, description="The only text the cards may come from: a lesson's transcript and/or summary.")
    title: str | None = None
    count: int = Field(8, ge=1, le=20)


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardsResponse(BaseModel):
    cards: list[Flashcard]


class QuizRequest(BaseModel):
    material: str = Field(..., min_length=1, description="The only text the questions may come from: a lesson's transcript and/or summary.")
    title: str | None = None
    count: int = Field(5, ge=1, le=15)
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str | None = None


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]
