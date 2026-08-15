from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.query import Citation


class RetrievedChunk(BaseModel):
    id: str | None = None
    text: str
    document_id: str | None = None
    document_name: str
    page: int
    score: float = 0.0


class ClassificationResult(BaseModel):
    intent: Literal["lookup", "comparison", "trend", "document_query", "clarification"]
    entities: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: str | None = None


class AnswerResult(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)

