from functools import lru_cache

from fastapi import Request

from app.agents.answer_generator import AnswerWorker
from app.agents.classifier import QueryClassifier
from app.agents.retriever import RetrievalWorker
from app.agents.supervisor import AgentOrchestrator
from app.agents.verifier import VerificationWorker
from app.core.config import get_settings
from app.core.observability import LangfuseTracer
from app.integrations.llm_client import GeminiLLMClient
from app.integrations.redis_client import RedisCache
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.services.document_service import DocumentService
from app.services.evaluation_service import EvaluationService
from app.services.query_service import QueryService
from app.tools.document_tool import build_document_tools
from app.tools.registry import ToolRegistry
from app.tools.retrieval_tool import build_retrieval_tool
from vectorstore import VectorStore


@lru_cache
def get_vector_repository() -> VectorRepository:
    settings = get_settings()
    return VectorRepository(VectorStore(settings.vector_db_path))


def get_document_repository(request: Request) -> DocumentRepository:
    return request.app.state.document_repository


def get_cache(request: Request) -> RedisCache:
    return request.app.state.redis_cache


def get_langgraph_checkpointer(request: Request):
    return request.app.state.langgraph_checkpointer


def get_langfuse_tracer(request: Request) -> LangfuseTracer:
    return request.app.state.langfuse_tracer


def get_document_service(request: Request) -> DocumentService:
    settings = get_settings()
    return DocumentService(settings, get_document_repository(request), get_vector_repository())


def get_query_service(request: Request) -> QueryService:
    documents = get_document_repository(request)
    vectors = get_vector_repository()
    tools = ToolRegistry()
    tools.register(build_retrieval_tool(vectors))
    for tool in build_document_tools(documents):
        tools.register(tool)
    llm_client = GeminiLLMClient(get_settings())
    orchestrator = AgentOrchestrator(
        QueryClassifier(llm_client),
        RetrievalWorker(tools),
        VerificationWorker(llm_client),
        AnswerWorker(llm_client),
        checkpointer=get_langgraph_checkpointer(request),
        langfuse_tracer=get_langfuse_tracer(request),
    )
    return QueryService(orchestrator, get_cache(request))


def get_evaluation_service(request: Request) -> EvaluationService:
    return EvaluationService(get_query_service(request))
