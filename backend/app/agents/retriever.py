from app.schemas.agent import ClassificationResult, RetrievedChunk
from app.tools.registry import ToolRegistry


class RetrievalWorker:
    def __init__(self, tools: ToolRegistry):
        self.tools = tools

    async def retrieve(self, query: str, classification: ClassificationResult) -> list[RetrievedChunk]:
        if classification.intent in {"comparison", "trend"} and classification.entities:
            chunks: list[RetrievedChunk] = []
            seen = set()
            for entity in classification.entities:
                results = await self.tools.invoke("search_documents", {"query": entity, "top_k": 3})
                for chunk in results:
                    key = (chunk.document_name, chunk.page, chunk.text[:80])
                    if key not in seen:
                        seen.add(key)
                        chunks.append(chunk)
            return chunks[:8]
        return await self.tools.invoke("search_documents", {"query": query, "top_k": 5})

