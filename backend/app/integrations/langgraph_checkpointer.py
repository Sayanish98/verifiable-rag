from typing import Any

from app.core.config import Settings
from app.core.logging import log_event


async def create_langgraph_checkpointer(settings: Settings) -> tuple[Any, Any | None]:
    """Create a durable LangGraph checkpointer when configured.

    Local development falls back to InMemorySaver. Production can set:

    LANGGRAPH_CHECKPOINTER=mongo
    MONGODB_URL=mongodb://...
    """
    if settings.langgraph_checkpointer.lower() == "mongo" and settings.mongodb_url:
        try:
            from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

            context = AsyncMongoDBSaver.from_conn_string(
                settings.mongodb_url,
                db_name=f"{settings.mongodb_database}_langgraph",
                checkpoint_collection_name="checkpoints",
                writes_collection_name="checkpoint_writes",
            )
            checkpointer = await context.__aenter__()
            log_event("langgraph_checkpointer_ready", backend="mongo")
            return checkpointer, context
        except Exception as exc:
            log_event("langgraph_checkpointer_fallback", backend="memory", error=str(exc))

    from langgraph.checkpoint.memory import InMemorySaver

    log_event("langgraph_checkpointer_ready", backend="memory")
    return InMemorySaver(), None


async def close_langgraph_checkpointer(context: Any | None) -> None:
    if context is not None:
        await context.__aexit__(None, None, None)

