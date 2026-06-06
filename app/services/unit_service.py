from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.unit_repo import UnitRepository


class UnitService:

    def __init__(self, session: AsyncSession):
        self.repo = UnitRepository(session)

    async def create(self, data: dict):
        return await self.repo.create_one(data)

    async def get(self, unit_uuid: UUID):
        return await self.repo.get_one(uuid=unit_uuid)

    async def get_all(self):
        return await self.repo.get_all()

    async def update(self, unit_uuid: UUID, data: dict):
        return await self.repo.update_one(unit_uuid, data)

    async def delete(self, unit_uuid: UUID):
        return await self.repo.delete_one(unit_uuid)