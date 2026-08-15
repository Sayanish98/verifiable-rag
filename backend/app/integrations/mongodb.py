from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings
from app.core.logging import log_event


async def create_mongodb(settings: Settings) -> AsyncIOMotorDatabase | None:
    if not settings.mongodb_url:
        return None
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
    try:
        await client.admin.command("ping")
    except Exception as exc:
        log_event("mongodb_unavailable", error=str(exc))
        return None
    database = client[settings.mongodb_database]
    await database.documents.create_index([("checksum", 1)], unique=True)
    await database.conversations.create_index([("user_id", 1), ("updated_at", -1)])
    await database.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    await database.ai_runs.create_index([("request_id", 1)], unique=True)
    await database.evaluations.create_index([("created_at", -1)])
    return database

