from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.services.supplier_service import SupplierService

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.get("", response_model=list[SupplierResponse])
async def get_suppliers(
    session: AsyncSession = Depends(get_session),
):
    service = SupplierService(session)
    return await service.get_all()


@router.get("/{supplier_uuid}", response_model=SupplierResponse)
async def get_supplier(
    supplier_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = SupplierService(session)
    return await service.get(supplier_uuid)


@router.post("", response_model=SupplierResponse)
async def create_supplier(
    payload: SupplierCreate,
    session: AsyncSession = Depends(get_session),
):
    service = SupplierService(session)

    async with session.begin():
        return await service.create(payload.model_dump())


@router.put("/{supplier_uuid}", response_model=SupplierResponse)
async def update_supplier(
    supplier_uuid: UUID,
    payload: SupplierUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = SupplierService(session)

    async with session.begin():
        return await service.update(
            supplier_uuid,
            payload.model_dump(exclude_unset=True),
        )


@router.delete("/{supplier_uuid}")
async def delete_supplier(
    supplier_uuid: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = SupplierService(session)

    async with session.begin():
        await service.delete(supplier_uuid)

    return {"success": True}