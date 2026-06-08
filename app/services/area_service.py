from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.area_repo import AreaRepository
from app.services.audit_service import AuditService

ENTITY = "area"


class AreaService:

    def __init__(self, session: AsyncSession):
        self.repo = AreaRepository(session)
        self.audit = AuditService(session)

    async def create(self, data: dict, user_uuid: UUID | None = None):
        row = await self.repo.create_one(data)
        await self.audit.log(user_uuid, "create", ENTITY, row.uuid, new_data=data)
        return row

    async def get(self, area_uuid: UUID):
        return await self.repo.get_one(uuid=area_uuid)

    async def get_all(self):
        return await self.repo.get_all()

    async def search(self, query: str, limit: int, offset: int):
        return await self.repo.search_by_name(query, limit, offset)

    async def update(self, area_uuid: UUID, data: dict, user_uuid: UUID | None = None):
        row = await self.repo.update_one(area_uuid, data)
        await self.audit.log(user_uuid, "update", ENTITY, area_uuid, new_data=data)
        return row

    async def delete(self, area_uuid: UUID, user_uuid: UUID | None = None):
        row = await self.repo.delete_one(area_uuid)
        await self.audit.log(user_uuid, "delete", ENTITY, area_uuid)
        return row
