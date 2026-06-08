from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pallet_repo import PalletRepository


class PalletService:

    def __init__(self, session: AsyncSession):
        self.repo = PalletRepository(session)

    async def list_stock(self) -> list[dict]:
        rows = await self.repo.get_all_with_relations()

        return [
            {
                "uuid": p.uuid,
                "supplier_uuid": p.supplier_uuid,
                "area_uuid": p.area_uuid,
                "unit_uuid": p.unit_uuid,
                "supplier_name": p.supplier.name,
                "area_name": p.area.name,
                "unit_name": p.unit.name,
                "quantity": p.quantity,
            }
            for p in rows
        ]

    async def get_stock_record(
        self,
        supplier_uuid: UUID,
        area_uuid: UUID,
        unit_uuid: UUID,
    ):
        return await self.repo.get_stock(supplier_uuid, area_uuid, unit_uuid)
