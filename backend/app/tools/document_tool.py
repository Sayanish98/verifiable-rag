from pydantic import BaseModel, Field

from app.repositories.document_repository import DocumentRepository
from app.tools.base import Tool, ToolDefinition


class DocumentIdInput(BaseModel):
    document_id: str = Field(min_length=1)


class EmptyInput(BaseModel):
    pass


def build_document_tools(repository: DocumentRepository) -> list[Tool]:
    async def get_metadata(arguments: dict):
        params = DocumentIdInput.model_validate(arguments)
        document = await repository.get(params.document_id)
        return document.model_dump(mode="json") if document else None

    async def list_documents(arguments: dict):
        EmptyInput.model_validate(arguments)
        return [doc.model_dump(mode="json") for doc in await repository.list()]

    return [
        Tool(
            ToolDefinition(
                name="get_document_metadata",
                description="Get upload, status and chunk metadata for one document.",
                input_schema=DocumentIdInput.model_json_schema(),
            ),
            get_metadata,
        ),
        Tool(
            ToolDefinition(
                name="list_uploaded_documents",
                description="List uploaded medical documents and ingestion statuses.",
                input_schema=EmptyInput.model_json_schema(),
            ),
            list_documents,
        ),
    ]

