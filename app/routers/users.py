from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exc import ForbiddenException
from app.database.session import get_session
from app.dependencies import require_permission
from app.models.user import User
from app.schemas.user import RoleOut, UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

# Admin-only user management (the "users" permission module).
router = APIRouter(tags=["Users"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_permission("users")),
):
    return await UserService(session).list_users()


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_permission("users")),
):
    return await UserService(session).list_roles()


@router.post("/users", response_model=UserOut)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_permission("users")),
):
    service = UserService(session)

    user = await service.create_user(
        payload.username, payload.password, payload.role, payload.must_change_password
    )
    await session.commit()
    return user


@router.put("/users/{user_uuid}", response_model=UserOut)
async def update_user(
    user_uuid: UUID,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("users")),
):
    if user_uuid == current_user.uuid and payload.is_active is False:
        raise ForbiddenException("You cannot deactivate your own account")

    service = UserService(session)

    user = await service.update_user(
        user_uuid,
        payload.username,
        payload.password,
        payload.role,
        payload.must_change_password,
        payload.is_active,
    )
    await session.commit()
    return user


@router.delete("/users/{user_uuid}")
async def delete_user(
    user_uuid: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("users")),
):
    if user_uuid == current_user.uuid:
        raise ForbiddenException("You cannot delete your own account")

    service = UserService(session)
    await service.delete_user(user_uuid)
    await session.commit()
    return {"success": True}

from sqlalchemy import text
@router.get("/debug-time")
async def debug_time(session: AsyncSession = Depends(get_session)):
    timezone = await session.execute(text("SHOW TIMEZONE"))
    now = await session.execute(text("SELECT NOW()"))
    local = await session.execute(text("SELECT CURRENT_TIMESTAMP"))

    return {
        "timezone": timezone.scalar(),
        "now": str(now.scalar()),
        "current_timestamp": str(local.scalar()),
    }