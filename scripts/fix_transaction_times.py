"""One-off fix for transactions whose created_at was stored in UTC.

Before the DB session timezone was set to Europe/Warsaw, UI-created transactions
got created_at from the server clock (UTC on Render) — i.e. 2 hours behind local
time in summer. Imported (Excel) transactions already had correct local time.

This script shifts created_at by +HOURS for transactions in a time window, so
you can correct only the affected (UTC) period without touching the older,
already-correct rows.

Usage:
    # preview how many rows would change
    python -m scripts.fix_transaction_times --from 2026-06-29 --dry-run

    # apply +2h to everything created from 29.06.2026 up to the fix deploy time
    python -m scripts.fix_transaction_times --from 2026-06-29 --until 2026-07-01T10:00

WARNING: run AFTER deploying the timezone fix, and set --until to the fix's
deploy time so newly-corrected rows are not shifted again.
"""
import argparse
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.transaction import Transaction


async def shift_created_at(session, start: datetime, end: datetime, hours: int, dry_run: bool) -> int:
    rows = (
        await session.execute(
            select(Transaction).where(
                Transaction.created_at >= start,
                Transaction.created_at < end,
            )
        )
    ).scalars().all()

    if not dry_run:
        delta = timedelta(hours=hours)
        for tx in rows:
            tx.created_at = tx.created_at + delta
        await session.commit()

    return len(rows)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


async def _main(start: datetime, end: datetime, hours: int, dry_run: bool) -> None:
    async with AsyncSessionLocal() as session:
        count = await shift_created_at(session, start, end, hours, dry_run)

    action = "Would shift" if dry_run else "Shifted"
    print(f"{action} {count} transactions by {hours:+d}h "
          f"(created_at in [{start}, {end}))")


def main() -> None:
    parser = argparse.ArgumentParser(description="Shift created_at for a time window.")
    parser.add_argument("--from", dest="start", required=True, type=_parse_dt,
                        help="Start of the buggy window, e.g. 2026-06-29 or 2026-06-29T00:00")
    parser.add_argument("--until", dest="end", type=_parse_dt, default=datetime.now(),
                        help="End of the window (exclusive); default: now")
    parser.add_argument("--hours", type=int, default=2, help="Hours to add (default 2 = summer offset)")
    parser.add_argument("--dry-run", action="store_true", help="Only count, do not modify")
    args = parser.parse_args()

    asyncio.run(_main(args.start, args.end, args.hours, args.dry_run))


if __name__ == "__main__":
    main()
