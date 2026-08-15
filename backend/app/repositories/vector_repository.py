import asyncio

from app.schemas.agent import RetrievedChunk
from vectorstore import VectorStore


class VectorRepository:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def document_exists(self, document_name: str) -> bool:
        return await asyncio.to_thread(self.vector_store.document_exists, document_name)

    async def add_chunk(self, chunk: dict) -> None:
        await asyncio.to_thread(self.vector_store.add_chunk, chunk)

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        chunks = await asyncio.to_thread(self.vector_store.similarity_search, query, top_k)
        return [
            RetrievedChunk(
                id=f"{chunk['doc_name']}:{chunk['page_number']}:{index}",
                text=chunk["text"],
                document_id=chunk.get("document_id") or chunk["doc_name"],
                document_name=chunk["doc_name"],
                page=chunk["page_number"],
                score=float(chunk.get("score", 0.0)),
            )
            for index, chunk in enumerate(chunks)
        ]

    async def delete_document(self, document_name: str) -> int:
        return await asyncio.to_thread(self.vector_store.delete_document, document_name)

