from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session):
        super().__init__(session, Transaction)

    async def get_with_relations(self, transaction_uuid):
        return await self.get_one(
            uuid=transaction_uuid,
            options=[
                joinedload(Transaction.supplier),
                joinedload(Transaction.area),
                joinedload(Transaction.unit),
                joinedload(Transaction.user),
            ],
        )

    async def get_all_with_relations(self):
        query = (
            select(Transaction)
            .options(
                joinedload(Transaction.supplier),
                joinedload(Transaction.area),
                joinedload(Transaction.unit),
                joinedload(Transaction.user),
            )
            .order_by(Transaction.created_at.desc())
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_by_period(
        self,
        date_from: datetime,
        date_to: datetime,
    ):
        query = (
            select(Transaction)
            .where(Transaction.created_at >= date_from)
            .where(Transaction.created_at <= date_to)
            .options(
                joinedload(Transaction.supplier),
                joinedload(Transaction.area),
                joinedload(Transaction.unit),
                joinedload(Transaction.user),
            )
            .order_by(Transaction.created_at.desc())
        )

        result = await self.session.execute(query)

        return result.scalars().all()