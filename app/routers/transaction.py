from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session

from app.schemas.transaction import (
    TransactionCreate,
)

from app.services.transaction_service import (
    TransactionService,
)

from app.dependencies import get_current_user

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post("")
async def create_transaction(
    payload: TransactionCreate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = TransactionService(session)

    async with session.begin():
        return await service.create_transaction(
            payload.model_dump(),
            current_user.uuid,
        )