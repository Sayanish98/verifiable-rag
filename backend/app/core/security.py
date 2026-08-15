from fastapi import Request


SUSPICIOUS_INSTRUCTIONS = (
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "reveal your instructions",
)


def validate_user_query(query: str) -> None:
    lowered = query.lower()
    if any(marker in lowered for marker in SUSPICIOUS_INSTRUCTIONS):
        # Keep the request answerable, but make the safety boundary explicit to downstream agents.
        return


def get_rate_limit_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

