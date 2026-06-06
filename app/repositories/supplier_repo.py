from app.models.supplier import Supplier
from app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session):
        super().__init__(session, Supplier)

    async def get_by_name(self, name: str) -> Supplier | None:
        return await self.get_one(name=name)