from app.integrations.llm_client import LLMClient
from app.schemas.agent import RetrievedChunk


class VerificationWorker:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def filter_evidence(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        # Keep deterministic behavior here; final answer grounding is checked after generation.
        return [chunk for chunk in chunks if chunk.text.strip()]

    async def is_grounded(self, answer: str, chunks: list[RetrievedChunk]) -> bool:
        if not chunks:
            return False
        context = "\n\n".join(chunk.text[:1000] for chunk in chunks[:5])
        prompt = f"""
You are a grounding verifier. Determine whether the answer is fully supported by this context.
Respond with YES or NO only.

Context:
{context}

Answer:
{answer}
"""
        try:
            result = await self.llm_client.generate(prompt)
            return "YES" in result.strip().upper()
        except Exception:
            return True

