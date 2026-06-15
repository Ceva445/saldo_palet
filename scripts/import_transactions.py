"""Import transactions from tbl_raport.xlsx into the database.

Resolves Pracownik/Dostawca/Jednostka/Obszar by name (run scripts.import_validate
first so they all exist), bulk-inserts a Transaction per valid row preserving the
original Data_dodania (created_at) and Data (operation_date), and recomputes the
pallet balances.

Usage:
    python -m scripts.import_validate          # first: create master data
    python -m scripts.import_transactions      # then: import the rows
    python -m scripts.import_transactions --force   # import even if transactions exist
"""
import argparse
import asyncio
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, insert, select

from app.core.database import AsyncSessionLocal
from app.models.area import Area
from app.models.pallet import Pallet
from app.models.supplier import Supplier
from app.models.transaction import Transaction
from app.models.unit import Unit
from app.models.user import User
from scripts._raport import OP_MAP, parse_workbook, quantity_of, row_errors

BATCH = 5000


async def _name_map(session, model, key="name"):
    rows = (await session.execute(select(model))).scalars()
    return {getattr(r, key): r.uuid for r in rows}


async def run_import(session, rows, force: bool = False, progress=None) -> dict:
    existing = (
        await session.execute(select(func.count()).select_from(Transaction))
    ).scalar()
    if existing and not force:
        raise SystemExit(
            f"W bazie jest już {existing} transakcji. Użyj --force, aby mimo to importować."
        )

    users = await _name_map(session, User, "username")
    suppliers = await _name_map(session, Supplier)
    units = await _name_map(session, Unit)
    areas = await _name_map(session, Area)

    valid = [r for r in rows if not row_errors(r)]
    valid.sort(key=lambda r: r.created_at)

    # One in-memory pass: build insert dicts + running balances (no per-row DB I/O).
    tx_dicts: list[dict] = []
    balances: dict[tuple, int] = {}
    missing_refs = 0
    now = datetime.now()

    for r in valid:
        try:
            s_uuid = suppliers[r.dostawca]
            a_uuid = areas[r.obszar]
            u_uuid = units[r.jednostka]
            user_uuid = users[r.pracownik]
        except KeyError:
            missing_refs += 1
            continue

        op = OP_MAP[r.operacja]
        # IN/OUT are positive counts; a correction is a signed delta.
        qty = int(r.wartosc) if op == "CORRECTION" else quantity_of(r)

        tx_dicts.append({
            "uuid": uuid4(),
            "type": op,
            "supplier_uuid": s_uuid,
            "area_uuid": a_uuid,
            "unit_uuid": u_uuid,
            "user_uuid": user_uuid,
            "quantity": qty,
            "comment": r.komentarz,
            "operation_date": r.operation_date,
            "created_at": r.created_at,
            "updated_at": r.created_at or now,
        })

        key = (s_uuid, a_uuid, u_uuid)
        current = balances.get(key, 0)
        # Receipts increase the debt (balance down); issues/corrections raise it.
        if op == "RECEIPT":
            current -= qty
        elif op == "ISSUE":
            current += qty
        else:  # CORRECTION is a signed delta
            current += qty
        balances[key] = current

    # Bulk insert transactions (Core executemany, batched).
    total = len(tx_dicts)
    for i in range(0, total, BATCH):
        chunk = tx_dicts[i:i + BATCH]
        await session.execute(insert(Transaction), chunk)
        await session.commit()
        if progress:
            progress(min(i + BATCH, total), total)

    # Recompute pallets: update existing, bulk-insert the rest (1 read + 1 write).
    existing_pallets = {
        (p.supplier_uuid, p.area_uuid, p.unit_uuid): p
        for p in (await session.execute(select(Pallet))).scalars()
    }
    new_pallets = []
    for (s_uuid, a_uuid, u_uuid), qty in balances.items():
        pallet = existing_pallets.get((s_uuid, a_uuid, u_uuid))
        if pallet:
            pallet.quantity = qty
        else:
            new_pallets.append({
                "uuid": uuid4(),
                "supplier_uuid": s_uuid,
                "area_uuid": a_uuid,
                "unit_uuid": u_uuid,
                "quantity": qty,
            })
    if new_pallets:
        await session.execute(insert(Pallet), new_pallets)
    await session.commit()

    return {
        "inserted": total,
        "skipped_invalid": len(rows) - len(valid),
        "skipped_missing_refs": missing_refs,
        "pallets": len(balances),
    }


async def _main(path: str, force: bool) -> None:
    print("Wczytywanie pliku…", flush=True)
    rows = parse_workbook(path)
    print(f"Wczytano wierszy: {len(rows)}", flush=True)

    def progress(done, total):
        pct = int(done * 100 / total) if total else 100
        print(f"\r  Import: {done}/{total} ({pct}%)", end="", flush=True)

    async with AsyncSessionLocal() as session:
        result = await run_import(session, rows, force=force, progress=progress)
    print()  # newline after progress

    print("=" * 60)
    print("IMPORT TRANSAKCJI — PODSUMOWANIE")
    print("=" * 60)
    print(f"Zaimportowano transakcji:        {result['inserted']}")
    print(f"Pominięto (błędne wiersze):      {result['skipped_invalid']}")
    print(f"Pominięto (brak masterdata):     {result['skipped_missing_refs']}")
    print(f"Zaktualizowano pozycji stanu:    {result['pallets']}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import transactions from raport file.")
    parser.add_argument("--file", default="tbl_raport.xlsx")
    parser.add_argument("--force", action="store_true", help="Import even if transactions already exist.")
    args = parser.parse_args()
    asyncio.run(_main(args.file, args.force))


if __name__ == "__main__":
    main()
