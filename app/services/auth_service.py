# Authentication service
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password
from app.repositories.user_repo import UserRepository
from app.services.permission_service import PermissionService


class AuthService:

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.permissions = PermissionService()

    def _serialize_user(self, user) -> dict:
        return {
            "uuid": str(user.uuid),
            "username": user.username,
            "role": user.role.name,
            "is_active": user.is_active,
            "permissions": self.permissions.allowed_modules(user.role.name),
        }

    async def login(self, username: str, password: str):
        user = await self.repo.get_by_username(username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        token = create_access_token({"sub": str(user.uuid)})

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": self._serialize_user(user),
        }

    async def register(self, username: str, password: str, role_uuid):
        user = await self.repo.create_one({
            "username": username,
            "hashed_password": hash_password(password),
            "role_uuid": role_uuid,
        })

        return user