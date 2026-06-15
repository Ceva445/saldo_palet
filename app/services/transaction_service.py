from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import BadRequestException
from app.models.transaction import TransactionType
from app.repositories.pallet_repo import PalletRepository
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.common import ActionResult
from app.services.audit_service import AuditService


class TransactionService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.pallet_repo = PalletRepository(session)
        self.audit = AuditService(session)

    async def create_transaction(self, data: dict, user_uuid) -> ActionResult:
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

        # Balance = pallets we owe the supplier (negative = debt).
        # Receiving goods means we owe pallets → balance goes down;
        # issuing (returning) pallets reduces the debt → balance goes up.
        if t_type == TransactionType.RECEIPT:
            pallet.quantity -= data["quantity"]

        elif t_type == TransactionType.ISSUE:
            pallet.quantity += data["quantity"]

        elif t_type == TransactionType.CORRECTION:
            # Delta adjustment (may be negative), not an absolute value.
            pallet.quantity += data["quantity"]

        else:
            raise BadRequestException("Invalid transaction type")

        transaction = await self.transaction_repo.create_one({
            "type": t_type,
            "supplier_uuid": data["supplier_uuid"],
            "area_uuid": data["area_uuid"],
            "unit_uuid": data["unit_uuid"],
            "quantity": data["quantity"],
            "comment": data.get("comment"),
            "operation_date": data.get("date") or date.today(),
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

        return ActionResult()
