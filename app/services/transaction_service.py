from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transaction_repo import TransactionRepository
from app.repositories.pallet_repo import PalletRepository


class TransactionService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.pallet_repo = PalletRepository(session)

    async def create_transaction(self, data: dict, user_uuid):

        pallet = await self.pallet_repo.get_one(
            supplier_uuid=data["supplier_uuid"],
            area_uuid=data["area_uuid"],
        )

        if not pallet:
            pallet = await self.pallet_repo.create_one({
                "supplier_uuid": data["supplier_uuid"],
                "area_uuid": data["area_uuid"],
                "quantity": 0,
            })

        t_type = data["type"]

        if t_type == "RECEIPT":
            pallet.quantity += data["quantity"]

        elif t_type == "ISSUE":
            if pallet.quantity < data["quantity"]:
                raise HTTPException(400, "Not enough stock")

            pallet.quantity -= data["quantity"]

        elif t_type == "CORRECTION":
            pallet.quantity = data["quantity"]

        else:
            raise HTTPException(400, "Invalid transaction type")

        await self.transaction_repo.create_one({
            **data,
            "user_uuid": user_uuid,
        })

        await self.session.flush()

        return {"status": "ok"}