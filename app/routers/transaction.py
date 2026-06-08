from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import BadRequestException, ForbiddenException
from app.database.session import get_session
from app.dependencies import get_current_user, permission_service
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

# Each transaction type maps to its own permission module / dashboard component.
TYPE_TO_MODULE = {
    TransactionType.RECEIPT.value: "receipts",
    TransactionType.ISSUE.value: "releases",
    TransactionType.CORRECTION.value: "corrections",
}


@router.post("")
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    module = TYPE_TO_MODULE.get(payload.type)
    if module is None:
        raise BadRequestException("Invalid transaction type")

    if not permission_service.has_access(current_user.role.name, module):
        raise ForbiddenException("Insufficient permissions")

    service = TransactionService(session)

    result = await service.create_transaction(
        payload.model_dump(),
        current_user.uuid,
    )
    await session.commit()
    return result
