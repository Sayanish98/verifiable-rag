import pytest

from app.core.config import Settings
from app.core.exceptions import InvalidLLMResponseError
from app.integrations.llm_client import GeminiLLMClient
from app.schemas.agent import ClassificationResult


class MalformedLLMClient(GeminiLLMClient):
    def __init__(self):
        super().__init__(Settings(GEMINI_API_KEY="test"))

    async def generate(self, prompt: str) -> str:
        return "not json"


@pytest.mark.asyncio
async def test_malformed_structured_llm_output_fails_controlled():
    client = MalformedLLMClient()

    with pytest.raises(InvalidLLMResponseError):
        await client.generate_structured("classify", ClassificationResult)

