from app.models.unit import Unit
from app.repositories.base import BaseRepository


class UnitRepository(BaseRepository[Unit]):
    def __init__(self, session):
        super().__init__(session, Unit)

    async def get_by_name(self, name: str) -> Unit | None:
        return await self.get_one(name=name)