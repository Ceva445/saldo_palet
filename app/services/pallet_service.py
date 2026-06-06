from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pallet_repo import PalletRepository


class PalletService:

    def __init__(self, session: AsyncSession):
        self.repo = PalletRepository(session)

    async def get_all(self):
        return await self.repo.get_all()

    async def get_stock_record(self, supplier_uuid: UUID, area_uuid: UUID):
        return await self.repo.get_one(
            supplier_uuid=supplier_uuid,
            area_uuid=area_uuid,
        )

    async def create_stock(self, supplier_uuid: UUID, area_uuid: UUID):
        return await self.repo.create_one({
            "supplier_uuid": supplier_uuid,
            "area_uuid": area_uuid,
            "quantity": 0,
        })