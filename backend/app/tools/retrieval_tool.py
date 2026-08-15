from pydantic import BaseModel, Field

from app.repositories.vector_repository import VectorRepository
from app.tools.base import Tool, ToolDefinition


class SearchDocumentsInput(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    document_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


def build_retrieval_tool(repository: VectorRepository) -> Tool:
    async def handler(arguments: dict):
        params = SearchDocumentsInput.model_validate(arguments)
        # document_ids is reserved for future metadata filtering; Chroma metadata currently stores names.
        return await repository.search(params.query, top_k=params.top_k)

    return Tool(
        ToolDefinition(
            name="search_documents",
            description="Search uploaded medical documents and return evidence chunks with page citations.",
            input_schema=SearchDocumentsInput.model_json_schema(),
        ),
        handler,
    )

