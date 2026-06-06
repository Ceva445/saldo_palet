from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.area_repo import AreaRepository


class AreaService:

    def __init__(self, session: AsyncSession):
        self.repo = AreaRepository(session)

    async def create(self, data: dict):
        return await self.repo.create_one(data)

    async def get(self, area_uuid: UUID):
        return await self.repo.get_one(uuid=area_uuid)

    async def get_all(self):
        return await self.repo.get_all()

    async def update(self, area_uuid: UUID, data: dict):
        return await self.repo.update_one(area_uuid, data)

    async def delete(self, area_uuid: UUID):
        return await self.repo.delete_one(area_uuid)