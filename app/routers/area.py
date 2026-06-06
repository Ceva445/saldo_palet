from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.area import (
    AreaCreate,
    AreaUpdate,
    AreaResponse,
)
from app.services.area_service import AreaService

router = APIRouter(
    prefix="/areas",
    tags=["Areas"],
)


@router.get("", response_model=list[AreaResponse])
async def get_areas(
    session: AsyncSession = Depends(get_session),
):
    service = AreaService(session)
    return await service.get_all()


@router.get("/{area_uuid}", response_model=AreaResponse)
async def get_area(
    area_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = AreaService(session)
    return await service.get(area_uuid)


@router.post("", response_model=AreaResponse)
async def create_area(
    payload: AreaCreate,
    session: AsyncSession = Depends(get_session),
):
    service = AreaService(session)

    async with session.begin():
        return await service.create(payload.model_dump())


@router.put("/{area_uuid}", response_model=AreaResponse)
async def update_area(
    area_uuid: UUID,
    payload: AreaUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = AreaService(session)

    async with session.begin():
        return await service.update(
            area_uuid,
            payload.model_dump(exclude_unset=True),
        )


@router.delete("/{area_uuid}")
async def delete_area(
    area_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = AreaService(session)

    async with session.begin():
        await service.delete(area_uuid)

    return {"success": True}