import pytest

from app.agents.classifier import QueryClassifier
from app.integrations.llm_client import FakeLLMClient


@pytest.mark.asyncio
async def test_ambiguous_query_requires_clarification():
    classifier = QueryClassifier(FakeLLMClient())

    result = await classifier.classify("it")

    assert result.requires_clarification is True
    assert result.intent == "clarification"

