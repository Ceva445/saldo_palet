# Authentication service
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token


class AuthService:

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def login(self, username: str, password: str):
        user = await self.repo.get_one(username=username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        token = create_access_token({"sub": str(user.uuid)})

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    async def register(self, username: str, password: str, role_uuid):
        user = await self.repo.create_one({
            "username": username,
            "hashed_password": hash_password(password),
            "role_uuid": role_uuid,
        })

        return user