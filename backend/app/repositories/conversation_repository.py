from datetime import datetime, timezone


class ConversationRepository:
    def __init__(self, database=None):
        self.database = database

    async def record_message(self, conversation_id: str, role: str, text: str, request_id: str) -> None:
        if self.database is None:
            return
        await self.database.messages.insert_one(
            {
                "conversation_id": conversation_id,
                "role": role,
                "text": text[:4000],
                "request_id": request_id,
                "created_at": datetime.now(timezone.utc),
            }
        )

