"""Validate tbl_raport.xlsx and ensure all referenced master data exists.

Creates missing Pracownik (users), Dostawca (suppliers), Jednostka (units) and
Obszar (areas), then writes a report of what was created and which rows have
problems.

Usage:
    python -m scripts.import_validate                         # create master data + report
    python -m scripts.import_validate --dry-run               # only analyse + report, no DB writes
    python -m scripts.import_validate --report bledy.txt      # custom report file

Run this BEFORE scripts.import_transactions.
"""
import argparse
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.area import Area
from app.models.role import Role
from app.models.supplier import Supplier
from app.models.unit import Unit
from app.models.user import User
from scripts._raport import parse_workbook, row_errors

ROLES = [
    ("admin", "Full access"),
    ("operator", "Receipts, releases and corrections"),
    ("viewer", "Read-only / reports"),
]
IMPORT_ROLE = "operator"


def analyze(rows) -> dict:
    """DB-independent analysis: errors, warnings, distinct master-data names."""
    errors = [(r.row_no, errs) for r in rows if (errs := row_errors(r))]

    units = {r.jednostka for r in rows if r.jednostka}
    areas = {r.obszar for r in rows if r.obszar}

    suppliers = {r.dostawca for r in rows if r.dostawca}
    users = {r.pracownik for r in rows if r.pracownik}

    warnings = []
    overlap = units & areas
    if overlap:
        warnings.append(f"Nazwy występują i jako Jednostka, i jako Obszar: {sorted(overlap)}")
    weird_ws = sorted(n for n in (suppliers | units | areas) if "  " in n)
    if weird_ws:
        warnings.append(f"Nazwy z podwójną spacją (możliwe duplikaty): {weird_ws}")

    # Case-insensitive collisions become separate rows (name uniqueness is case-sensitive).
    for label, names in (("Pracownik", users), ("Dostawca", suppliers)):
        groups = {}
        for n in names:
            groups.setdefault(n.lower(), []).append(n)
        dupes = [sorted(v) for v in groups.values() if len(v) > 1]
        if dupes:
            warnings.append(f"{label}: różna wielkość liter w tej samej nazwie (powstaną osobne wpisy): {dupes}")

    return {
        "total_rows": len(rows),
        "valid_rows": len(rows) - len(errors),
        "errors": errors,
        "warnings": warnings,
        "distinct": {
            "users": sorted({r.pracownik for r in rows if r.pracownik}),
            "suppliers": sorted({r.dostawca for r in rows if r.dostawca}),
            "units": sorted(units),
            "areas": sorted(areas),
        },
    }


async def _ensure_roles(session):
    existing = {r.name for r in (await session.execute(select(Role))).scalars()}
    for name, desc in ROLES:
        if name not in existing:
            session.add(Role(name=name, description=desc))
    await session.flush()
    return (
        await session.execute(select(Role).where(Role.name == IMPORT_ROLE))
    ).scalar_one()


async def run_validate(session, rows) -> dict:
    report = analyze(rows)
    role = await _ensure_roles(session)
    distinct = report["distinct"]

    existing_users = {u.username for u in (await session.execute(select(User))).scalars()}
    existing_suppliers = {s.name for s in (await session.execute(select(Supplier))).scalars()}
    existing_units = {u.name for u in (await session.execute(select(Unit))).scalars()}
    existing_areas = {a.name for a in (await session.execute(select(Area))).scalars()}

    created = {"users": [], "suppliers": [], "units": [], "areas": []}

    for name in distinct["users"]:
        if name not in existing_users:
            # Imported users get a shared password "123" and must change it on first login.
            session.add(User(
                username=name,
                hashed_password=hash_password("123"),
                role_uuid=role.uuid,
                is_active=True,
                must_change_password=True,
            ))
            created["users"].append(name)
    for name in distinct["suppliers"]:
        if name not in existing_suppliers:
            session.add(Supplier(name=name))
            created["suppliers"].append(name)
    for name in distinct["units"]:
        if name not in existing_units:
            session.add(Unit(name=name))
            created["units"].append(name)
    for name in distinct["areas"]:
        if name not in existing_areas:
            session.add(Area(name=name))
            created["areas"].append(name)

    await session.commit()

    report["created"] = created
    return report


def write_report(path: str, report: dict, source: str, dry_run: bool) -> None:
    lines = []
    lines.append("=" * 60)
    lines.append("RAPORT WALIDACJI IMPORTU" + (" (DRY-RUN, bez zapisu do bazy)" if dry_run else ""))
    lines.append("=" * 60)
    lines.append(f"Plik źródłowy: {source}")
    lines.append(f"Wierszy w pliku: {report['total_rows']}")
    lines.append(f"Wierszy gotowych do importu: {report['valid_rows']}")
    lines.append(f"Wierszy do pominięcia: {len(report['errors'])}")
    lines.append("")

    d = report["distinct"]
    created = report.get("created")
    label = "Utworzono" if created is not None else "Rozpoznano (do utworzenia)"
    lines.append(f"MASTERDATA — {label}:")
    for kind in ("users", "suppliers", "units", "areas"):
        if created is not None:
            names = created[kind]
            lines.append(f"  {kind}: utworzono {len(names)} (rozpoznano {len(d[kind])})")
        else:
            names = d[kind]
            lines.append(f"  {kind}: {len(names)}")
        for n in names:
            lines.append(f"      + {n}")
    lines.append("")

    if report["warnings"]:
        lines.append("OSTRZEŻENIA (co może pójść nie tak):")
        for w in report["warnings"]:
            lines.append(f"  ! {w}")
        lines.append("")

    lines.append(f"BŁĘDNE WIERSZE ({len(report['errors'])}):")
    for row_no, errs in report["errors"]:
        lines.append(f"  wiersz {row_no}: {', '.join(errs)}")
    lines.append("=" * 60)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


async def _main(path: str, report_path: str, dry_run: bool) -> None:
    rows = parse_workbook(path)

    if dry_run:
        report = analyze(rows)
    else:
        async with AsyncSessionLocal() as session:
            report = await run_validate(session, rows)

    write_report(report_path, report, source=path, dry_run=dry_run)

    created = report.get("created")
    print(f"Wierszy: {report['total_rows']}, gotowych: {report['valid_rows']}, "
          f"do pominięcia: {len(report['errors'])}")
    if created is not None:
        print("Utworzono: "
              f"users={len(created['users'])}, suppliers={len(created['suppliers'])}, "
              f"units={len(created['units'])}, areas={len(created['areas'])}")
    for w in report["warnings"]:
        print(f"  ! {w}")
    print(f"Szczegółowy raport zapisano do: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate raport and create missing master data.")
    parser.add_argument("--file", default="tbl_raport.xlsx")
    parser.add_argument("--report", default="validate_report.txt")
    parser.add_argument("--dry-run", action="store_true", help="Only analyse and write the report; no DB writes.")
    args = parser.parse_args()
    asyncio.run(_main(args.file, args.report, args.dry_run))


if __name__ == "__main__":
    main()
