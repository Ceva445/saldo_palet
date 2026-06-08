from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import BadRequestException
from app.models.transaction import TransactionType
from app.repositories.pallet_repo import PalletRepository
from app.repositories.transaction_repo import TransactionRepository
from app.services.audit_service import AuditService


class TransactionService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.pallet_repo = PalletRepository(session)
        self.audit = AuditService(session)

    async def create_transaction(self, data: dict, user_uuid):
        # Stock is tracked per (supplier, area, unit) — the unit must be part of the key.
        pallet = await self.pallet_repo.get_stock(
            supplier_uuid=data["supplier_uuid"],
            area_uuid=data["area_uuid"],
            unit_uuid=data["unit_uuid"],
        )

        if not pallet:
            pallet = await self.pallet_repo.create_one({
                "supplier_uuid": data["supplier_uuid"],
                "area_uuid": data["area_uuid"],
                "unit_uuid": data["unit_uuid"],
                "quantity": 0,
            })

        t_type = data["type"]

        if t_type == TransactionType.RECEIPT:
            pallet.quantity += data["quantity"]

        elif t_type == TransactionType.ISSUE:
            if pallet.quantity < data["quantity"]:
                raise BadRequestException("Not enough stock")

            pallet.quantity -= data["quantity"]

        elif t_type == TransactionType.CORRECTION:
            pallet.quantity = data["quantity"]

        else:
            raise BadRequestException("Invalid transaction type")

        transaction = await self.transaction_repo.create_one({
            **data,
            "user_uuid": user_uuid,
        })

        await self.audit.log(
            user_uuid,
            action=t_type,
            entity_name="transaction",
            entity_uuid=transaction.uuid,
            new_data={"type": t_type, "quantity": data["quantity"]},
        )

        await self.session.flush()

        return {"status": "ok"}
