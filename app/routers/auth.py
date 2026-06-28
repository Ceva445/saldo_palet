from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import UnauthorizedException
from app.database.session import get_session
from app.dependencies import get_current_user, permission_service
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Login endpoint that returns access token and user info."""
    service = AuthService(session)
    result = await service.login(payload.username, payload.password)

    if not result:
        raise UnauthorizedException("Invalid username or password")

    return result


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return the current user and the modules they may access (for UI gating)."""
    return {
        "uuid": current_user.uuid,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "role": current_user.role.name,
        "permissions": permission_service.allowed_modules(current_user.role.name),
        "must_change_password": current_user.must_change_password,
    }


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password and clear the must-change flag."""
    service = AuthService(session)
    await service.change_password(current_user, payload.old_password, payload.new_password)
    await session.commit()
    return {"success": True}
