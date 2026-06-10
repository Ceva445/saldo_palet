"""(Re)create the pallets and transactions tables from the models.

Useful when those two tables were dropped manually: Alembic still thinks the DB
is at head, so `alembic upgrade head` won't recreate them. This builds them from
the current models (same schema as head) and is safe to re-run — existing tables
are left untouched (checkfirst=True).

Usage:
    python -m scripts.create_tables
"""
import asyncio

from app.core.database import engine
from app.models.base import Base
from app.models.pallet import Pallet
from app.models.transaction import Transaction

TABLES = [Pallet.__table__, Transaction.__table__]


async def main() -> None:
    async with engine.begin() as conn:
        # checkfirst=True (default): only creates tables that are missing.
        await conn.run_sync(Base.metadata.create_all, tables=TABLES, checkfirst=True)
    print("OK — sprawdzono/utworzono tabele: pallets, transactions")


if __name__ == "__main__":
    asyncio.run(main())
