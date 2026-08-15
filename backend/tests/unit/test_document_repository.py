import pytest

from app.core.exceptions import DuplicateDocumentError
from app.repositories.document_repository import DocumentRepository


@pytest.mark.asyncio
async def test_checksum_uniqueness_prevents_duplicate_uploads():
    repository = DocumentRepository()

    await repository.create_pending("first.pdf", "sha256abc")

    with pytest.raises(DuplicateDocumentError):
        await repository.create_pending("second-name.pdf", "sha256abc")

