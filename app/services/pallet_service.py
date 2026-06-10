from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pallet_repo import PalletRepository
from app.schemas.pallet import PalletResponse


class PalletService:

    def __init__(self, session: AsyncSession):
        self.repo = PalletRepository(session)

    async def list_stock(self) -> list[PalletResponse]:
        rows = await self.repo.get_all_with_relations()
        return [
            PalletResponse(
                uuid=p.uuid,
                supplier_uuid=p.supplier_uuid,
                area_uuid=p.area_uuid,
                unit_uuid=p.unit_uuid,
                supplier_name=p.supplier.name,
                area_name=p.area.name,
                unit_name=p.unit.name,
                quantity=p.quantity,
            )
            for p in rows
        ]
