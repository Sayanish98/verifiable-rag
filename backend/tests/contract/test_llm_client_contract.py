import pytest

from app.integrations.llm_client import FakeLLMClient
from app.schemas.agent import ClassificationResult


@pytest.mark.asyncio
async def test_llm_client_structured_output_matches_contract():
    client = FakeLLMClient()

    result = await client.generate_structured("classify this", ClassificationResult)

    assert result.intent == "lookup"
    assert result.requires_clarification is False

