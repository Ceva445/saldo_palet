from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.pallet import PalletResponse
from app.services.pallet_service import PalletService

router = APIRouter(
    prefix="/pallets",
    tags=["Pallets"],
)


@router.get("", response_model=list[PalletResponse])
async def get_stock(
    session: AsyncSession = Depends(get_session),
):
    service = PalletService(session)
    return await service.get_all()