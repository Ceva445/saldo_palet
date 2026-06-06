from app.models.area import Area
from app.repositories.base import BaseRepository


class AreaRepository(BaseRepository[Area]):
    def __init__(self, session):
        super().__init__(session, Area)

    async def get_by_name(self, name: str) -> Area | None:
        return await self.get_one(name=name)