"""Seed roles and an initial admin user.

Usage:
    python -m scripts.seed_data

Idempotent: re-running will not create duplicates.
"""
import asyncio
import os

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User

ROLES = [
    ("admin", "Full access to all modules"),
    ("operator", "Receipts, releases and corrections"),
    ("viewer", "Read-only / reports"),
]

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        roles: dict[str, Role] = {}

        for name, description in ROLES:
            role = (
                await session.execute(select(Role).where(Role.name == name))
            ).scalar_one_or_none()

            if role is None:
                role = Role(name=name, description=description)
                session.add(role)
                await session.flush()

            roles[name] = role

        admin = (
            await session.execute(
                select(User).where(User.username == ADMIN_USERNAME)
            )
        ).scalar_one_or_none()

        if admin is None:
            session.add(
                User(
                    username=ADMIN_USERNAME,
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    role_uuid=roles["admin"].uuid,
                    is_active=True,
                )
            )
            print(f"Created admin user '{ADMIN_USERNAME}'.")
        else:
            print(f"Admin user '{ADMIN_USERNAME}' already exists.")

        await session.commit()

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
