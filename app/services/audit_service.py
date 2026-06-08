from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repo import AuditLogRepository


class AuditService:
    """Records who changed what. Skips silently when no user is supplied
    (e.g. internal calls / unit tests)."""

    def __init__(self, session: AsyncSession):
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        user_uuid: UUID | None,
        action: str,
        entity_name: str,
        entity_uuid: UUID,
        old_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        if user_uuid is None:
            return

        await self.repo.create_one({
            "user_uuid": user_uuid,
            "action": action,
            "entity_name": entity_name,
            "entity_uuid": entity_uuid,
            "old_data": old_data,
            "new_data": new_data,
        })
