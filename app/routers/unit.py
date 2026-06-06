from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.unit import (
    UnitCreate,
    UnitUpdate,
    UnitResponse,
)
from app.services.unit_service import UnitService

router = APIRouter(
    prefix="/units",
    tags=["Units"],
)


@router.get("", response_model=list[UnitResponse])
async def get_units(
    session: AsyncSession = Depends(get_session),
):
    service = UnitService(session)
    return await service.get_all()


@router.get("/{unit_uuid}", response_model=UnitResponse)
async def get_unit(
    unit_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = UnitService(session)
    return await service.get(unit_uuid)


@router.post("", response_model=UnitResponse)
async def create_unit(
    payload: UnitCreate,
    session: AsyncSession = Depends(get_session),
):
    service = UnitService(session)

    async with session.begin():
        return await service.create(payload.model_dump())


@router.put("/{unit_uuid}", response_model=UnitResponse)
async def update_unit(
    unit_uuid: UUID,
    payload: UnitUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = UnitService(session)

    async with session.begin():
        return await service.update(
            unit_uuid,
            payload.model_dump(exclude_unset=True),
        )


@router.delete("/{unit_uuid}")
async def delete_unit(
    unit_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = UnitService(session)

    async with session.begin():
        await service.delete(unit_uuid)

    return {"success": True}