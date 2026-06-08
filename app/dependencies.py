# Dependency injection module
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import ForbiddenException, UnauthorizedException
from app.core.jwt import decode_access_token
from app.database.session import get_session
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.permission_service import PermissionService

security = HTTPBearer()

permission_service = PermissionService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated user (with role eager-loaded) from the JWT."""
    try:
        payload = decode_access_token(credentials.credentials)
        user_uuid = UUID(payload.get("sub"))
    except Exception:
        raise UnauthorizedException("Invalid token")

    user = await UserRepository(session).get_with_role(user_uuid)

    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise ForbiddenException("User is inactive")

    return user


def require_permission(module: str):
    """Dependency factory enforcing role access to a module at the API level."""

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not permission_service.has_access(current_user.role.name, module):
            raise ForbiddenException("Insufficient permissions")
        return current_user

    return dependency
