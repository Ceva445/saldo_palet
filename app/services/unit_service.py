from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import ObjectAlreadyExistsException
from app.repositories.unit_repo import UnitRepository
from app.schemas.unit import UnitResponse
from app.services.audit_service import AuditService

ENTITY = "unit"


class UnitService:

    def __init__(self, session: AsyncSession):
        self.repo = UnitRepository(session)
        self.audit = AuditService(session)

    async def create(self, data: dict, user_uuid: UUID | None = None) -> UnitResponse:
        if await self.repo.get_by_name(data["name"]):
            raise ObjectAlreadyExistsException("Dane już istnieją")
        row = await self.repo.create_one(data)
        await self.audit.log(user_uuid, "create", ENTITY, row.uuid, new_data=data)
        return UnitResponse.model_validate(row)

    async def get(self, unit_uuid: UUID) -> UnitResponse | None:
        row = await self.repo.get_one(uuid=unit_uuid)
        return UnitResponse.model_validate(row) if row else None

    async def get_all(self) -> list[UnitResponse]:
        rows = await self.repo.get_all()
        return [UnitResponse.model_validate(r) for r in rows]

    async def search(self, query: str, limit: int, offset: int) -> tuple[list[UnitResponse], int]:
        rows, total = await self.repo.search_by_name(query, limit, offset)
        return [UnitResponse.model_validate(r) for r in rows], total

    async def update(self, unit_uuid: UUID, data: dict, user_uuid: UUID | None = None) -> UnitResponse:
        row = await self.repo.update_one(unit_uuid, data)
        await self.audit.log(user_uuid, "update", ENTITY, unit_uuid, new_data=data)
        return UnitResponse.model_validate(row)

    async def delete(self, unit_uuid: UUID, user_uuid: UUID | None = None) -> UnitResponse:
        row = await self.repo.delete_one(unit_uuid)
        await self.audit.log(user_uuid, "delete", ENTITY, unit_uuid)
        return UnitResponse.model_validate(row)
