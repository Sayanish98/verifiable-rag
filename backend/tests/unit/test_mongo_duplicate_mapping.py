import pytest
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import DuplicateDocumentError
from app.repositories.document_repository import DocumentRepository


class DuplicateCollection:
    async def insert_one(self, document):
        raise DuplicateKeyError("duplicate checksum")


class FakeDatabase:
    documents = DuplicateCollection()


@pytest.mark.asyncio
async def test_mongo_duplicate_key_maps_to_domain_error():
    repository = DocumentRepository(FakeDatabase())

    with pytest.raises(DuplicateDocumentError):
        await repository.create_pending("duplicate.pdf", "same-sha")

