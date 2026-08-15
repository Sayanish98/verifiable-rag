from uuid import UUID

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    type: str
    text: str


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    stream: bool = False


class Citation(BaseModel):
    document_id: str
    document_name: str
    page: int
    snippet: str
    score: float = 0.0


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float = Field(ge=0, le=1)
    request_id: str
    thread_id: str | None = None
    requires_human_review: bool = False


class ResumeRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=128)
    approved: bool = True
    comment: str | None = Field(default=None, max_length=1000)


class GraphStateResponse(BaseModel):
    thread_id: str
    values: dict
    next: list[str]
    checkpoint_id: str | None = None


class LegacyQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_history: list[dict] | None = None
