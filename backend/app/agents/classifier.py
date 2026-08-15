from app.integrations.llm_client import LLMClient
from app.schemas.agent import ClassificationResult


class QueryClassifier:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def classify(self, query: str) -> ClassificationResult:
        if len(query.split()) <= 2 and query.lower() in {"it", "that", "this", "them"}:
            return ClassificationResult(
                intent="clarification",
                requires_clarification=True,
                clarification_question="Which document or medical value are you asking about?",
            )

        prompt = f"""
You are classifying a query for a medical document RAG system.

Classify the user's request into one of:
- lookup
- comparison
- trend
- document_query
- clarification

Only use clarification for vague pronouns with no usable document or medical context.

Query: {query}
"""
        result = await self.llm_client.generate_structured(prompt, ClassificationResult)
        if not result.entities and result.intent != "clarification":
            result.entities.append(query)
        return result

