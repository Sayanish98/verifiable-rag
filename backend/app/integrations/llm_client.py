import asyncio
import json
import os
import time
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.exceptions import InvalidLLMResponseError, LLMProviderError
from app.core.observability import LLM_REQUEST_DURATION, LLM_REQUESTS_TOTAL, PROMETHEUS_AVAILABLE

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    async def generate(self, prompt: str) -> str: ...

    async def generate_structured(self, prompt: str, schema: type[T]) -> T: ...


class GeminiLLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            api_key = self.settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise LLMProviderError("GEMINI_API_KEY is not configured")
            self._client = genai.Client(api_key=api_key)
        return self._client

    async def generate(self, prompt: str) -> str:
        started = time.perf_counter()
        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._get_client().models.generate_content,
                        model=self.settings.llm_model,
                        contents=prompt,
                    ),
                    timeout=self.settings.llm_timeout_seconds,
                )
                if PROMETHEUS_AVAILABLE:
                    LLM_REQUESTS_TOTAL.labels(status="success").inc()
                    LLM_REQUEST_DURATION.labels(status="success").observe(time.perf_counter() - started)
                return response.text.strip()
            except Exception as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    break
                await asyncio.sleep(0.25 * (2**attempt))
        if PROMETHEUS_AVAILABLE:
            LLM_REQUESTS_TOTAL.labels(status="error").inc()
            LLM_REQUEST_DURATION.labels(status="error").observe(time.perf_counter() - started)
        raise LLMProviderError(str(last_error) if last_error else "LLM request failed")

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        schema_prompt = (
            f"{prompt}\n\nReturn only valid JSON matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}"
        )
        last_validation_error: Exception | None = None
        for _ in range(2):
            text = await self.generate(schema_prompt)
            try:
                payload = _extract_json(text)
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_validation_error = exc
                schema_prompt += "\nYour previous response was invalid JSON. Return corrected JSON only."
        raise InvalidLLMResponseError(str(last_validation_error))


class FakeLLMClient:
    async def generate(self, prompt: str) -> str:
        return "I cannot find sufficient information in your uploaded documents to answer confidently."

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        defaults: dict[str, Any] = {
            "intent": "lookup",
            "entities": [],
            "requires_clarification": False,
            "clarification_question": None,
        }
        return schema.model_validate(defaults)


def _extract_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found")
    return json.loads(cleaned[start : end + 1])
