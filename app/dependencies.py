# Dependency injection module
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import decode_access_token
from app.database.session import get_session
from app.repositories.user_repo import UserRepository
from app.services.permission_service import PermissionService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
):
    """Get the current authenticated user from the JWT token."""
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)
        user_uuid: str = payload.get("sub")
        
        if user_uuid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    repo = UserRepository(session)
    user = await repo.get_one(uuid=user_uuid)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    
    return user


def require_permission(module: str):
    """Dependency to check user has permission for a specific module."""
    async def dependency(current_user = Depends(get_current_user)):
        permission_service = PermissionService()
        if not permission_service.has_access(current_user.role.name, module):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return dependency
