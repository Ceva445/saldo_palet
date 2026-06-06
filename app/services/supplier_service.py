from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.supplier_repo import SupplierRepository


class SupplierService:

    def __init__(self, session: AsyncSession):
        self.repo = SupplierRepository(session)

    async def create(self, data: dict):
        return await self.repo.create_one(data)

    async def get(self, supplier_uuid: UUID):
        return await self.repo.get_one(uuid=supplier_uuid)

    async def get_all(self):
        return await self.repo.get_all()

    async def update(self, supplier_uuid: UUID, data: dict):
        return await self.repo.update_one(supplier_uuid, data)

    async def delete(self, supplier_uuid: UUID):
        return await self.repo.delete_one(supplier_uuid)