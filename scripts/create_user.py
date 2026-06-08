"""Create a single user in the configured database.

Usage:
    python -m scripts.create_user --username jan --password secret --role operator

Roles must already exist (run `python -m scripts.seed_data` first).
"""
import argparse
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


async def create_user(
    username: str,
    password: str,
    role_name: str,
    force: bool = False,
) -> None:
    async with AsyncSessionLocal() as session:
        role = (
            await session.execute(select(Role).where(Role.name == role_name))
        ).scalar_one_or_none()

        if role is None:
            raise SystemExit(
                f"Role '{role_name}' not found. Run `python -m scripts.seed_data` first."
            )

        existing = (
            await session.execute(select(User).where(User.username == username))
        ).scalar_one_or_none()

        if existing is not None:
            if not force:
                raise SystemExit(
                    f"User '{username}' already exists. Use --force to reset password/role."
                )
            existing.hashed_password = hash_password(password)
            existing.role_uuid = role.uuid
            existing.is_active = True
            await session.commit()
            print(f"Updated user '{username}' (role '{role_name}', password reset).")
            return

        session.add(
            User(
                username=username,
                hashed_password=hash_password(password),
                role_uuid=role.uuid,
                is_active=True,
            )
        )
        await session.commit()

    print(f"Created user '{username}' with role '{role_name}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an application user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--role",
        default="operator",
        choices=["admin", "operator", "viewer"],
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset password/role if the user already exists.",
    )
    args = parser.parse_args()

    asyncio.run(create_user(args.username, args.password, args.role, args.force))


if __name__ == "__main__":
    main()
