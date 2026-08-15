from typing import TypedDict


class AgentState(TypedDict):
    request_id: str
    thread_id: str
    query: str
    intent: str | None
    document_ids: list[str]
    entities: list[str]
    retrieved_chunks: list[dict]
    verified_chunks: list[dict]
    answer: str | None
    citations: list[dict]
    confidence: float
    retrieval_attempts: int
    retry_count: int
    evidence_score: float
    error: str | None
    requires_human_review: bool
    errors: list[str]
