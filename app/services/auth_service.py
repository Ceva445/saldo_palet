# Authentication service
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import BadRequestException, ForbiddenException
from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginResponse, UserResponse
from app.services.permission_service import PermissionService


class AuthService:

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.permissions = PermissionService()

    def _user_response(self, user) -> UserResponse:
        return UserResponse(
            uuid=user.uuid,
            username=user.username,
            role=user.role.name,
            is_active=user.is_active,
            permissions=self.permissions.allowed_modules(user.role.name),
            must_change_password=user.must_change_password,
        )

    async def login(self, username: str, password: str) -> LoginResponse | None:
        user = await self.repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            raise ForbiddenException("Konto jest nieaktywne")

        token = create_access_token({"sub": str(user.uuid)})
        return LoginResponse(access_token=token, user=self._user_response(user))

    async def change_password(self, user, old_password: str, new_password: str) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise BadRequestException("Nieprawidłowe stare hasło")
        if not new_password:
            raise BadRequestException("Nowe hasło jest wymagane")

        await self.repo.update_one(
            user.uuid,
            {"hashed_password": hash_password(new_password), "must_change_password": False},
        )
