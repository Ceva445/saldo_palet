from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.schemas.unit import (
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)
from app.services.unit_service import UnitService

router = APIRouter(
    prefix="/units",
    tags=["Units"],
)


@router.get("", response_model=list[UnitResponse])
async def get_units(
    response: Response,
    search: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = UnitService(session)
    if search is not None or limit is not None:
        items, total = await service.search(search or "", limit or 50, offset)
        response.headers["X-Total-Count"] = str(total)
        return items
    return await service.get_all()


@router.get("/{unit_uuid}", response_model=UnitResponse)
async def get_unit(
    unit_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = UnitService(session)
    return await service.get(unit_uuid)


@router.post("", response_model=UnitResponse)
async def create_unit(
    payload: UnitCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = UnitService(session)

    row = await service.create(payload.model_dump(), current_user.uuid)
    await session.commit()
    return row


@router.put("/{unit_uuid}", response_model=UnitResponse)
async def update_unit(
    unit_uuid: UUID,
    payload: UnitUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = UnitService(session)

    row = await service.update(
        unit_uuid,
        payload.model_dump(exclude_unset=True),
        current_user.uuid,
    )
    await session.commit()
    return row


@router.delete("/{unit_uuid}")
async def delete_unit(
    unit_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = UnitService(session)

    await service.delete(unit_uuid, current_user.uuid)
    await session.commit()

    return {"success": True}
