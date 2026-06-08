from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.schemas.area import (
    AreaCreate,
    AreaResponse,
    AreaUpdate,
)
from app.services.area_service import AreaService

router = APIRouter(
    prefix="/areas",
    tags=["Areas"],
)


@router.get("", response_model=list[AreaResponse])
async def get_areas(
    response: Response,
    search: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = AreaService(session)
    if search is not None or limit is not None:
        items, total = await service.search(search or "", limit or 50, offset)
        response.headers["X-Total-Count"] = str(total)
        return items
    return await service.get_all()


@router.get("/{area_uuid}", response_model=AreaResponse)
async def get_area(
    area_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = AreaService(session)
    return await service.get(area_uuid)


@router.post("", response_model=AreaResponse)
async def create_area(
    payload: AreaCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = AreaService(session)

    row = await service.create(payload.model_dump(), current_user.uuid)
    await session.commit()
    return row


@router.put("/{area_uuid}", response_model=AreaResponse)
async def update_area(
    area_uuid: UUID,
    payload: AreaUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = AreaService(session)

    row = await service.update(
        area_uuid,
        payload.model_dump(exclude_unset=True),
        current_user.uuid,
    )
    await session.commit()
    return row


@router.delete("/{area_uuid}")
async def delete_area(
    area_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = AreaService(session)

    await service.delete(area_uuid, current_user.uuid)
    await session.commit()

    return {"success": True}
