import hashlib
import time

from app.agents.supervisor import AgentOrchestrator
from app.core.logging import log_event
from app.core.observability import record_cache_hit
from app.core.security import validate_user_query
from app.integrations.redis_client import RedisCache
from app.schemas.query import QueryRequest, QueryResponse


class QueryService:
    def __init__(self, orchestrator: AgentOrchestrator, cache: RedisCache):
        self.orchestrator = orchestrator
        self.cache = cache

    async def execute(self, request: QueryRequest, request_id: str) -> QueryResponse:
        started = time.perf_counter()
        validate_user_query(request.query)
        thread_id = request.thread_id or (str(request.conversation_id) if request.conversation_id else None)
        cache_key = self._cache_key(request.query)
        cached = None if thread_id else await self.cache.get_json(cache_key)
        if cached:
            cached["request_id"] = request_id
            cached["thread_id"] = thread_id
            log_event("query_cache_hit", request_id=request_id)
            record_cache_hit(True)
            return QueryResponse.model_validate(cached)

        log_event("query_cache_miss", request_id=request_id)
        record_cache_hit(False)
        response = await self.orchestrator.run(request.query, request_id, thread_id=thread_id)
        if not thread_id and not response.requires_human_review:
            await self.cache.set_json(cache_key, response.model_dump(mode="json"))
        log_event(
            "rag_query_completed",
            request_id=request_id,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
            chunks=len(response.citations),
            success=True,
        )
        return response

    async def stream(self, request: QueryRequest, request_id: str):
        validate_user_query(request.query)
        thread_id = request.thread_id or (str(request.conversation_id) if request.conversation_id else None)
        async for event in self.orchestrator.stream(request.query, request_id, thread_id=thread_id):
            yield event

    async def resume(self, thread_id: str, request_id: str, approved: bool, comment: str | None = None) -> QueryResponse:
        return await self.orchestrator.resume(thread_id, request_id, approved, comment)

    async def get_state(self, thread_id: str):
        return await self.orchestrator.get_state(thread_id)

    def _cache_key(self, query: str) -> str:
        digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
        return f"rag:v1:all_documents:{digest}"
