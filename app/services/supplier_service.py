from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.supplier_repo import SupplierRepository
from app.services.audit_service import AuditService

ENTITY = "supplier"


class SupplierService:

    def __init__(self, session: AsyncSession):
        self.repo = SupplierRepository(session)
        self.audit = AuditService(session)

    async def create(self, data: dict, user_uuid: UUID | None = None):
        row = await self.repo.create_one(data)
        await self.audit.log(user_uuid, "create", ENTITY, row.uuid, new_data=data)
        return row

    async def get(self, supplier_uuid: UUID):
        return await self.repo.get_one(uuid=supplier_uuid)

    async def get_all(self):
        return await self.repo.get_all()

    async def search(self, query: str, limit: int, offset: int):
        return await self.repo.search_by_name(query, limit, offset)

    async def update(self, supplier_uuid: UUID, data: dict, user_uuid: UUID | None = None):
        row = await self.repo.update_one(supplier_uuid, data)
        await self.audit.log(user_uuid, "update", ENTITY, supplier_uuid, new_data=data)
        return row

    async def delete(self, supplier_uuid: UUID, user_uuid: UUID | None = None):
        row = await self.repo.delete_one(supplier_uuid)
        await self.audit.log(user_uuid, "delete", ENTITY, supplier_uuid)
        return row
