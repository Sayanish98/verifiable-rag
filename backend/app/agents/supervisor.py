import time
from collections.abc import AsyncIterator
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.agents.answer_generator import AnswerWorker
from app.agents.classifier import QueryClassifier
from app.agents.retriever import RetrievalWorker
from app.agents.state import AgentState
from app.agents.verifier import VerificationWorker
from app.core.observability import (
    AGENT_RUN_DURATION,
    AGENT_RUNS_TOTAL,
    PROMETHEUS_AVAILABLE,
    LangfuseTracer,
    observe_span,
    record_agent_retry,
    record_retrieval,
)
from app.schemas.agent import ClassificationResult, RetrievedChunk
from app.schemas.query import Citation, GraphStateResponse, QueryResponse


class AgentOrchestrator:
    def __init__(
        self,
        classifier: QueryClassifier,
        retriever: RetrievalWorker,
        verifier: VerificationWorker,
        answer_worker: AnswerWorker,
        *,
        checkpointer,
        langfuse_tracer: LangfuseTracer,
    ):
        self.classifier = classifier
        self.retriever = retriever
        self.verifier = verifier
        self.answer_worker = answer_worker
        self.langfuse = langfuse_tracer
        self.graph = self._build_graph().compile(checkpointer=checkpointer)

    async def run(self, query: str, request_id: str, thread_id: str | None = None) -> QueryResponse:
        started = time.perf_counter()
        thread_id = thread_id or f"thread_{request_id}"
        config = self._config(thread_id)
        initial_state = self._initial_state(query, request_id, thread_id)

        async with observe_span("agent.run", request_id=request_id, thread_id=thread_id):
            result = await self.graph.ainvoke(initial_state, config=config)

        response = self._response_from_state(result, request_id, thread_id)
        if PROMETHEUS_AVAILABLE:
            status = "human_review" if response.requires_human_review else "success"
            AGENT_RUNS_TOTAL.labels(status=status).inc()
            AGENT_RUN_DURATION.labels(status=status).observe(time.perf_counter() - started)
        return response

    async def resume(self, thread_id: str, request_id: str, approved: bool, comment: str | None = None) -> QueryResponse:
        config = self._config(thread_id)
        result = await self.graph.ainvoke(
            Command(resume={"approved": approved, "comment": comment}),
            config=config,
        )
        return self._response_from_state(result, request_id, thread_id)

    async def get_state(self, thread_id: str) -> GraphStateResponse:
        snapshot = self.graph.get_state(self._config(thread_id))
        checkpoint_id = None
        if snapshot.config:
            checkpoint_id = snapshot.config.get("configurable", {}).get("checkpoint_id")
        return GraphStateResponse(
            thread_id=thread_id,
            values=_json_safe(snapshot.values),
            next=list(snapshot.next),
            checkpoint_id=checkpoint_id,
        )

    async def stream(self, query: str, request_id: str, thread_id: str | None = None) -> AsyncIterator[tuple[str, dict]]:
        thread_id = thread_id or f"thread_{request_id}"
        yield "status", {"stage": "langgraph_started", "request_id": request_id, "thread_id": thread_id}
        response = await self.run(query, request_id, thread_id)
        if response.requires_human_review:
            yield "human_review", response.model_dump(mode="json")
            return
        yield "status", {"stage": "answering", "request_id": request_id, "thread_id": thread_id}
        async for token in self.answer_worker.stream_tokens(response.answer):
            yield "token", {"text": token}
        yield "complete", response.model_dump(mode="json")

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("classify_query", self._classify_query)
        graph.add_node("ask_clarification", self._ask_clarification)
        graph.add_node("retrieve_documents", self._retrieve_documents)
        graph.add_node("verify_evidence", self._verify_evidence)
        graph.add_node("rewrite_query", self._rewrite_query)
        graph.add_node("human_review", self._human_review)
        graph.add_node("insufficient_evidence", self._insufficient_evidence)
        graph.add_node("generate_answer", self._generate_answer)
        graph.add_node("validate_answer", self._validate_answer)

        graph.add_edge(START, "classify_query")
        graph.add_conditional_edges(
            "classify_query",
            self._route_after_classification,
            {"clarification": "ask_clarification", "retrieve": "retrieve_documents"},
        )
        graph.add_edge("ask_clarification", END)
        graph.add_edge("retrieve_documents", "verify_evidence")
        graph.add_conditional_edges(
            "verify_evidence",
            self._route_after_verification,
            {
                "rewrite_query": "rewrite_query",
                "human_review": "human_review",
                "insufficient_evidence": "insufficient_evidence",
                "generate": "generate_answer",
            },
        )
        graph.add_edge("rewrite_query", "retrieve_documents")
        graph.add_edge("human_review", "generate_answer")
        graph.add_edge("insufficient_evidence", END)
        graph.add_edge("generate_answer", "validate_answer")
        graph.add_conditional_edges(
            "validate_answer",
            self._route_after_validation,
            {"retry_answer": "generate_answer", "end": END},
        )
        return graph

    async def _classify_query(self, state: AgentState) -> dict:
        async with observe_span("langgraph.classify", request_id=state["request_id"], thread_id=state["thread_id"]):
            classification = await self.classifier.classify(state["query"])
        self.langfuse.trace_agent_step(
            "classifier",
            request_id=state["request_id"],
            thread_id=state["thread_id"],
            metadata={"intent": classification.intent, "entity_count": len(classification.entities)},
        )
        return {
            "intent": classification.intent,
            "entities": classification.entities,
            "error": classification.clarification_question if classification.requires_clarification else None,
        }

    async def _ask_clarification(self, state: AgentState) -> dict:
        return {
            "answer": state["error"] or "Could you clarify your question?",
            "citations": [],
            "confidence": 0.0,
        }

    async def _retrieve_documents(self, state: AgentState) -> dict:
        classification = _classification_from_state(state)
        started = time.perf_counter()
        async with observe_span(
            "langgraph.retrieve",
            request_id=state["request_id"],
            thread_id=state["thread_id"],
            attempt=state["retrieval_attempts"] + 1,
        ):
            chunks = await self.retriever.retrieve(state["query"], classification)
        duration = time.perf_counter() - started
        record_retrieval(duration, len(chunks))
        self.langfuse.trace_agent_step(
            "retriever",
            request_id=state["request_id"],
            thread_id=state["thread_id"],
            metadata={"results_count": len(chunks), "attempt": state["retrieval_attempts"] + 1},
        )
        return {
            "retrieval_attempts": state["retrieval_attempts"] + 1,
            "retrieved_chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        }

    async def _verify_evidence(self, state: AgentState) -> dict:
        chunks = [RetrievedChunk.model_validate(chunk) for chunk in state["retrieved_chunks"]]
        async with observe_span("langgraph.verify", request_id=state["request_id"], thread_id=state["thread_id"]):
            verified = await self.verifier.filter_evidence(state["query"], chunks)
        evidence_score = min(1.0, len(verified) / 3)
        suspicious = _contains_prompt_injection_marker(state["query"]) or any(
            _contains_prompt_injection_marker(chunk.text) for chunk in verified
        )
        self.langfuse.trace_agent_step(
            "verifier",
            request_id=state["request_id"],
            thread_id=state["thread_id"],
            metadata={"evidence_score": evidence_score, "suspicious": suspicious},
        )
        return {
            "verified_chunks": [chunk.model_dump(mode="json") for chunk in verified],
            "evidence_score": evidence_score,
            "requires_human_review": suspicious,
        }

    async def _rewrite_query(self, state: AgentState) -> dict:
        record_agent_retry("retriever")
        rewritten = f"{state['query']} {' '.join(state['entities'])}".strip()
        return {
            "query": rewritten,
            "retry_count": state["retry_count"] + 1,
            "error": "Evidence score was low; query rewritten for one more retrieval attempt.",
        }

    async def _human_review(self, state: AgentState) -> dict:
        decision = interrupt(
            {
                "question": "Potential prompt-injection or unsafe document content detected. Approve answer generation?",
                "request_id": state["request_id"],
                "thread_id": state["thread_id"],
                "evidence_score": state["evidence_score"],
                "retrieved_chunks": len(state["verified_chunks"]),
            }
        )
        approved = decision.get("approved", bool(decision)) if isinstance(decision, dict) else bool(decision)
        if approved:
            return {"requires_human_review": False}
        return {
            "answer": "This run was stopped for human review and was not approved for answer generation.",
            "citations": [],
            "confidence": 0.0,
            "verified_chunks": [],
            "requires_human_review": False,
        }

    async def _insufficient_evidence(self, state: AgentState) -> dict:
        return {
            "answer": (
                "I cannot find sufficient verified evidence in your uploaded documents to answer this question. "
                "Please upload more relevant documents or rephrase the request."
            ),
            "citations": [],
            "confidence": 0.0,
            "error": "INSUFFICIENT_EVIDENCE",
        }

    async def _generate_answer(self, state: AgentState) -> dict:
        if state.get("answer") and not state["verified_chunks"]:
            return {}
        classification = _classification_from_state(state)
        chunks = [RetrievedChunk.model_validate(chunk) for chunk in state["verified_chunks"]]
        async with observe_span("langgraph.answer", request_id=state["request_id"], thread_id=state["thread_id"]):
            answer = await self.answer_worker.generate(state["query"], classification, chunks)
        self.langfuse.trace_agent_step(
            "answer_generator",
            request_id=state["request_id"],
            thread_id=state["thread_id"],
            metadata={"citation_count": len(answer.citations), "confidence": answer.confidence},
        )
        return {
            "answer": answer.answer,
            "citations": [citation.model_dump(mode="json") for citation in answer.citations],
            "confidence": answer.confidence,
        }

    async def _validate_answer(self, state: AgentState) -> dict:
        if not state["answer"] or not state["verified_chunks"]:
            return {}
        chunks = [RetrievedChunk.model_validate(chunk) for chunk in state["verified_chunks"]]
        grounded = await self.verifier.is_grounded(state["answer"], chunks)
        if grounded:
            return {"error": None}
        record_agent_retry("answer_generator")
        next_retry = state["retry_count"] + 1
        if next_retry >= 2:
            return {
                "answer": (
                    "I cannot provide a reliable answer from your uploaded documents. "
                    "The generated response failed grounding validation."
                ),
                "citations": [],
                "confidence": 0.0,
                "error": "ANSWER_NOT_GROUNDED",
            }
        return {"retry_count": next_retry, "error": "ANSWER_NOT_GROUNDED"}

    def _route_after_classification(self, state: AgentState) -> Literal["clarification", "retrieve"]:
        return "clarification" if state["intent"] == "clarification" else "retrieve"

    def _route_after_verification(
        self, state: AgentState
    ) -> Literal["rewrite_query", "human_review", "insufficient_evidence", "generate"]:
        if state["requires_human_review"]:
            return "human_review"
        if state["evidence_score"] >= 0.7:
            return "generate"
        if state["retrieval_attempts"] < 2:
            return "rewrite_query"
        return "insufficient_evidence"

    def _route_after_validation(self, state: AgentState) -> Literal["retry_answer", "end"]:
        if state["error"] == "ANSWER_NOT_GROUNDED" and state["retry_count"] < 2:
            return "retry_answer"
        return "end"

    def _response_from_state(self, state: dict[str, Any], request_id: str, thread_id: str) -> QueryResponse:
        if "__interrupt__" in state:
            return QueryResponse(
                answer="This run is paused for human review. Resume it after approval or rejection.",
                citations=[],
                confidence=0.0,
                request_id=request_id,
                thread_id=thread_id,
                requires_human_review=True,
            )
        return QueryResponse(
            answer=state.get("answer") or "No answer was generated.",
            citations=[Citation.model_validate(citation) for citation in state.get("citations", [])],
            confidence=state.get("confidence", 0.0),
            request_id=request_id,
            thread_id=thread_id,
            requires_human_review=state.get("requires_human_review", False),
        )

    def _initial_state(self, query: str, request_id: str, thread_id: str) -> AgentState:
        return {
            "request_id": request_id,
            "thread_id": thread_id,
            "query": query,
            "intent": None,
            "document_ids": [],
            "entities": [],
            "retrieved_chunks": [],
            "verified_chunks": [],
            "answer": None,
            "citations": [],
            "confidence": 0.0,
            "retrieval_attempts": 0,
            "retry_count": 0,
            "evidence_score": 0.0,
            "error": None,
            "requires_human_review": False,
            "errors": [],
        }

    def _config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}


def _classification_from_state(state: AgentState) -> ClassificationResult:
    return ClassificationResult(
        intent=state["intent"] or "lookup",
        entities=state["entities"] or [state["query"]],
        requires_clarification=state["intent"] == "clarification",
        clarification_question=state["error"],
    )


def _contains_prompt_injection_marker(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            "ignore previous instructions",
            "reveal your instructions",
            "system prompt",
            "developer message",
        )
    )


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items() if key != "__interrupt__"}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value
