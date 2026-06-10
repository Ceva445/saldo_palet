from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.supplier_repo import SupplierRepository
from app.schemas.supplier import SupplierResponse
from app.services.audit_service import AuditService

ENTITY = "supplier"


class SupplierService:

    def __init__(self, session: AsyncSession):
        self.repo = SupplierRepository(session)
        self.audit = AuditService(session)

    async def create(self, data: dict, user_uuid: UUID | None = None) -> SupplierResponse:
        row = await self.repo.create_one(data)
        await self.audit.log(user_uuid, "create", ENTITY, row.uuid, new_data=data)
        return SupplierResponse.model_validate(row)

    async def get(self, supplier_uuid: UUID) -> SupplierResponse | None:
        row = await self.repo.get_one(uuid=supplier_uuid)
        return SupplierResponse.model_validate(row) if row else None

    async def get_all(self) -> list[SupplierResponse]:
        rows = await self.repo.get_all()
        return [SupplierResponse.model_validate(r) for r in rows]

    async def search(self, query: str, limit: int, offset: int) -> tuple[list[SupplierResponse], int]:
        rows, total = await self.repo.search_by_name(query, limit, offset)
        return [SupplierResponse.model_validate(r) for r in rows], total

    async def update(self, supplier_uuid: UUID, data: dict, user_uuid: UUID | None = None) -> SupplierResponse:
        row = await self.repo.update_one(supplier_uuid, data)
        await self.audit.log(user_uuid, "update", ENTITY, supplier_uuid, new_data=data)
        return SupplierResponse.model_validate(row)

    async def delete(self, supplier_uuid: UUID, user_uuid: UUID | None = None) -> SupplierResponse:
        row = await self.repo.delete_one(supplier_uuid)
        await self.audit.log(user_uuid, "delete", ENTITY, supplier_uuid)
        return SupplierResponse.model_validate(row)
