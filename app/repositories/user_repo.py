from sqlalchemy.orm import joinedload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        return await self.get_one(
            username=username,
            options=[
                joinedload(User.role),
            ],
        )

    async def get_with_role(self, user_uuid):
        return await self.get_one(
            uuid=user_uuid,
            options=[
                joinedload(User.role),
            ],
        )