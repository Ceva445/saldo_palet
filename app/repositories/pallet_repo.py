from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.pallet import Pallet
from app.repositories.base import BaseRepository


class PalletRepository(BaseRepository[Pallet]):
    def __init__(self, session):
        super().__init__(session, Pallet)

    async def get_stock(
        self,
        supplier_uuid: UUID,
        area_uuid: UUID,
    ) -> Pallet | None:
        return await self.get_one(
            supplier_uuid=supplier_uuid,
            area_uuid=area_uuid,
        )

    async def get_all_with_relations(self):
        query = (
            select(Pallet)
            .options(
                joinedload(Pallet.supplier),
                joinedload(Pallet.area),
            )
        )

        result = await self.session.execute(query)

        return result.scalars().all()