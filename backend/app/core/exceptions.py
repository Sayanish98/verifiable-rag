from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400


class DuplicateDocumentError(AppError):
    def __init__(self, message: str = "Document already exists"):
        super().__init__("DOCUMENT_ALREADY_EXISTS", message, 409)


class LLMProviderError(AppError):
    def __init__(self, message: str = "LLM provider failed"):
        super().__init__("LLM_PROVIDER_ERROR", message, 503)


class InvalidLLMResponseError(AppError):
    def __init__(self, message: str = "LLM returned invalid structured output"):
        super().__init__("INVALID_LLM_RESPONSE", message, 502)

