from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from app.services.supplier_service import SupplierService

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.get("", response_model=list[SupplierResponse])
async def get_suppliers(
    response: Response,
    search: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = SupplierService(session)
    if search is not None or limit is not None:
        items, total = await service.search(search or "", limit or 50, offset)
        response.headers["X-Total-Count"] = str(total)
        return items
    return await service.get_all()


@router.get("/{supplier_uuid}", response_model=SupplierResponse)
async def get_supplier(
    supplier_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    service = SupplierService(session)
    return await service.get(supplier_uuid)


@router.post("", response_model=SupplierResponse)
async def create_supplier(
    payload: SupplierCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = SupplierService(session)

    row = await service.create(payload.model_dump(), current_user.uuid)
    await session.commit()
    return row


@router.put("/{supplier_uuid}", response_model=SupplierResponse)
async def update_supplier(
    supplier_uuid: UUID,
    payload: SupplierUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = SupplierService(session)

    row = await service.update(
        supplier_uuid,
        payload.model_dump(exclude_unset=True),
        current_user.uuid,
    )
    await session.commit()
    return row


@router.delete("/{supplier_uuid}")
async def delete_supplier(
    supplier_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("masterdata")),
):
    service = SupplierService(session)

    await service.delete(supplier_uuid, current_user.uuid)
    await session.commit()

    return {"success": True}
