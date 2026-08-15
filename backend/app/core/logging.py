import json
import logging
import sys
from typing import Any


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def log_event(event: str, **fields: Any) -> None:
    safe_fields = {key: value for key, value in fields.items() if value is not None}
    logging.getLogger("verifiable_rag").info(json.dumps({"event": event, **safe_fields}, default=str))

