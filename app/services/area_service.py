from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import ObjectAlreadyExistsException
from app.repositories.area_repo import AreaRepository
from app.schemas.area import AreaResponse
from app.services.audit_service import AuditService

ENTITY = "area"


class AreaService:

    def __init__(self, session: AsyncSession):
        self.repo = AreaRepository(session)
        self.audit = AuditService(session)

    async def create(self, data: dict, user_uuid: UUID | None = None) -> AreaResponse:
        if await self.repo.get_by_name(data["name"]):
            raise ObjectAlreadyExistsException("Dane już istnieją")
        row = await self.repo.create_one(data)
        await self.audit.log(user_uuid, "create", ENTITY, row.uuid, new_data=data)
        return AreaResponse.model_validate(row)

    async def get(self, area_uuid: UUID) -> AreaResponse | None:
        row = await self.repo.get_one(uuid=area_uuid)
        return AreaResponse.model_validate(row) if row else None

    async def get_all(self) -> list[AreaResponse]:
        rows = await self.repo.get_all()
        return [AreaResponse.model_validate(r) for r in rows]

    async def search(self, query: str, limit: int, offset: int) -> tuple[list[AreaResponse], int]:
        rows, total = await self.repo.search_by_name(query, limit, offset)
        return [AreaResponse.model_validate(r) for r in rows], total

    async def update(self, area_uuid: UUID, data: dict, user_uuid: UUID | None = None) -> AreaResponse:
        row = await self.repo.update_one(area_uuid, data)
        await self.audit.log(user_uuid, "update", ENTITY, area_uuid, new_data=data)
        return AreaResponse.model_validate(row)

    async def delete(self, area_uuid: UUID, user_uuid: UUID | None = None) -> AreaResponse:
        row = await self.repo.delete_one(area_uuid)
        await self.audit.log(user_uuid, "delete", ENTITY, area_uuid)
        return AreaResponse.model_validate(row)
