from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import FileRow
from ..domain.models import FileRecord


class FileRepository:
    def __init__(self, session: AsyncSession, user_id: str | None = None):
        self.session = session
        self.user_id = user_id

    async def create(self, record: FileRecord, storage_path: str) -> FileRecord:
        self.session.add(
            FileRow(
                id=record.id,
                user_id=self.user_id,
                trip_id=record.trip_id,
                original_name=record.original_name,
                stored_name=record.stored_name,
                storage_path=storage_path,
                mime_type=record.mime_type,
                size_bytes=record.size_bytes,
                status=record.status,
                created_at=record.created_at,
            )
        )
        await self.session.commit()
        return record

    async def get_row(self, file_id: str) -> FileRow | None:
        statement = select(FileRow).where(FileRow.id == file_id)
        if self.user_id is not None:
            statement = statement.where(FileRow.user_id == self.user_id)
        return await self.session.scalar(statement)

    async def get(self, file_id: str) -> FileRecord | None:
        row = await self.get_row(file_id)
        if not row:
            return None
        return FileRecord(
            id=row.id,
            trip_id=row.trip_id,
            original_name=row.original_name,
            stored_name=row.stored_name,
            mime_type=row.mime_type,
            size_bytes=row.size_bytes,
            status=row.status,
            created_at=row.created_at,
        )
