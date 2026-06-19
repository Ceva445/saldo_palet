"""Rebuild the pallets (balances) table from the transactions ledger.

Use after changing the balance convention or whenever pallet balances might be
out of sync. Works for both imported and UI-entered transactions.

Balance per (supplier, area, unit):
    sum(-quantity for RECEIPT) + sum(quantity for ISSUE) + sum(quantity for CORRECTION)
(all deltas are additive, so order does not matter).

Usage:
    python -m scripts.recompute_pallets
"""
import asyncio
from uuid import uuid4

from sqlalchemy import case, func, insert, select

from app.core.database import AsyncSessionLocal
from app.models.pallet import Pallet
from app.models.transaction import Transaction, TransactionType


async def recompute(session) -> int:
    t = Transaction
    movement = func.sum(
        case(
            (t.type == TransactionType.RECEIPT.value, -t.quantity),
            (t.type == TransactionType.ISSUE.value, t.quantity),
            (t.type == TransactionType.CORRECTION.value, t.quantity),
            else_=0,
        )
    )

    query = select(
        t.supplier_uuid, t.area_uuid, t.unit_uuid, movement
    ).group_by(t.supplier_uuid, t.area_uuid, t.unit_uuid)
    groups = (await session.execute(query)).all()

    # Keep opening_balance intact; only recompute the movement part (quantity).
    existing = {
        (p.supplier_uuid, p.area_uuid, p.unit_uuid): p
        for p in (await session.execute(select(Pallet))).scalars()
    }
    for pallet in existing.values():
        pallet.quantity = 0

    new_pallets = []
    for s_uuid, a_uuid, u_uuid, bal in groups:
        pallet = existing.get((s_uuid, a_uuid, u_uuid))
        if pallet:
            pallet.quantity = int(bal or 0)
        else:
            new_pallets.append({
                "uuid": uuid4(),
                "supplier_uuid": s_uuid,
                "area_uuid": a_uuid,
                "unit_uuid": u_uuid,
                "quantity": int(bal or 0),
            })

    if new_pallets:
        await session.execute(insert(Pallet), new_pallets)
    await session.commit()

    return len(existing) + len(new_pallets)


async def _main() -> None:
    async with AsyncSessionLocal() as session:
        count = await recompute(session)
    print(f"Recomputed {count} pallet balances from transactions.")


if __name__ == "__main__":
    asyncio.run(_main())
