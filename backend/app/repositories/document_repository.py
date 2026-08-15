from datetime import datetime, timezone
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from app.core.exceptions import DuplicateDocumentError
from app.schemas.document import DocumentMetadata, DocumentStatus


class DocumentRepository:
    def __init__(self, database=None):
        self.database = database
        self._memory: dict[str, DocumentMetadata] = {}
        self._checksum_index: dict[str, str] = {}

    async def create_pending(self, filename: str, checksum: str) -> DocumentMetadata:
        now = datetime.now(timezone.utc)
        document = DocumentMetadata(
            id=str(uuid4()),
            filename=filename,
            checksum=checksum,
            status=DocumentStatus.pending,
            created_at=now,
            updated_at=now,
        )
        if self.database is None:
            if checksum in self._checksum_index:
                raise DuplicateDocumentError("A document with the same content already exists")
            self._memory[document.id] = document
            self._checksum_index[checksum] = document.id
            return document

        try:
            await self.database.documents.insert_one(
                {
                    "_id": document.id,
                    "filename": filename,
                    "checksum": checksum,
                    "status": document.status,
                    "chunk_count": 0,
                    "page_count": 0,
                    "error_code": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except DuplicateKeyError as exc:
            raise DuplicateDocumentError("A document with the same content already exists") from exc
        return document

    async def get(self, document_id: str) -> DocumentMetadata | None:
        if self.database is None:
            return self._memory.get(document_id)
        raw = await self.database.documents.find_one({"_id": document_id})
        return _document_from_mongo(raw) if raw else None

    async def list(self) -> list[DocumentMetadata]:
        if self.database is None:
            return list(self._memory.values())
        cursor = self.database.documents.find({}).sort("created_at", -1)
        return [_document_from_mongo(raw) async for raw in cursor]

    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        *,
        chunk_count: int | None = None,
        page_count: int | None = None,
        error_code: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        if self.database is None:
            document = self._memory[document_id]
            self._memory[document_id] = document.model_copy(
                update={
                    "status": status,
                    "chunk_count": chunk_count if chunk_count is not None else document.chunk_count,
                    "page_count": page_count if page_count is not None else document.page_count,
                    "error_code": error_code,
                    "updated_at": now,
                }
            )
            return
        update = {"status": status, "updated_at": now, "error_code": error_code}
        if chunk_count is not None:
            update["chunk_count"] = chunk_count
        if page_count is not None:
            update["page_count"] = page_count
        await self.database.documents.update_one({"_id": document_id}, {"$set": update})


def _document_from_mongo(raw: dict) -> DocumentMetadata:
    return DocumentMetadata(
        id=raw["_id"],
        filename=raw["filename"],
        checksum=raw["checksum"],
        status=raw["status"],
        chunk_count=raw.get("chunk_count", 0),
        page_count=raw.get("page_count", 0),
        error_code=raw.get("error_code"),
        created_at=raw["created_at"],
        updated_at=raw["updated_at"],
    )

