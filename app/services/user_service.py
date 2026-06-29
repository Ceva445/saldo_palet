from uuid import UUID

from app.core.exc import BadRequestException, ObjectNotFoundException
from app.core.security import hash_password
from app.models.role import Role
from app.repositories.role_repo import RoleRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import RoleOut, UserOut


class UserService:

    def __init__(self, session):
        self.repo = UserRepository(session)
        self.role_repo = RoleRepository(session)

    async def list_users(self) -> list[UserOut]:
        users = await self.repo.get_all_with_roles()
        return [
            UserOut(
                uuid=u.uuid, username=u.username, role=u.role.name,
                is_active=u.is_active, must_change_password=u.must_change_password,
            )
            for u in users
        ]

    async def list_roles(self) -> list[RoleOut]:
        roles = await self.role_repo.get_all(order_by=[Role.name])
        return [RoleOut.model_validate(r) for r in roles]

    async def create_user(
        self,
        username: str,
        password: str,
        role_name: str,
        must_change_password: bool = False,
    ) -> UserOut:
        username = username.strip()
        if not username or not password:
            raise BadRequestException("Username and password are required")

        role = await self.role_repo.get_by_name(role_name)
        if role is None:
            raise BadRequestException(f"Role '{role_name}' not found")

        if await self.repo.get_by_username(username):
            raise BadRequestException("User already exists")

        user = await self.repo.create_one({
            "username": username,
            "hashed_password": hash_password(password),
            "role_uuid": role.uuid,
            "is_active": True,
            "must_change_password": must_change_password,
        })

        return UserOut(
            uuid=user.uuid, username=user.username, role=role.name,
            is_active=user.is_active, must_change_password=user.must_change_password,
        )

    async def update_user(
        self,
        user_uuid: UUID,
        username: str | None = None,
        password: str | None = None,
        role_name: str | None = None,
        must_change_password: bool | None = None,
        is_active: bool | None = None,
    ) -> UserOut:
        user = await self.repo.get_with_role(user_uuid)
        if user is None:
            raise ObjectNotFoundException("User not found")

        update: dict = {}
        new_username = user.username
        role_label = user.role.name
        flag = user.must_change_password
        active = user.is_active

        if username is not None:
            new_username = username.strip()
            if not new_username:
                raise BadRequestException("Username cannot be empty")
            if new_username != user.username:
                if await self.repo.get_by_username(new_username):
                    raise BadRequestException("User already exists")
                update["username"] = new_username

        if password:
            update["hashed_password"] = hash_password(password)

        if role_name is not None:
            role = await self.role_repo.get_by_name(role_name)
            if role is None:
                raise BadRequestException(f"Role '{role_name}' not found")
            update["role_uuid"] = role.uuid
            role_label = role.name

        if must_change_password is not None:
            update["must_change_password"] = must_change_password
            flag = must_change_password

        if is_active is not None:
            update["is_active"] = is_active
            active = is_active

        if update:
            await self.repo.update_one(user_uuid, update)

        return UserOut(
            uuid=user_uuid, username=new_username, role=role_label,
            is_active=active, must_change_password=flag,
        )

    async def delete_user(self, user_uuid: UUID) -> None:
        user = await self.repo.get_one(uuid=user_uuid)
        if user is None:
            raise ObjectNotFoundException("User not found")
        await self.repo.delete_one(user_uuid)
