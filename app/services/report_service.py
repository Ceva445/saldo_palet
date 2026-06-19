from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.models.pallet import Pallet
from app.models.supplier import Supplier
from app.models.transaction import Transaction, TransactionType
from app.models.unit import Unit
from app.models.user import User

OPERATION_LABELS = {
    TransactionType.RECEIPT.value: "IN",
    TransactionType.ISSUE.value: "OUT",
    TransactionType.CORRECTION.value: "KOREKTA",
}

HISTORY_HEADERS = [
    "Data_dodania", "Data", "Pracownik", "Dostawca", "Operacja",
    "Wartosc", "Jednostka", "Obszar", "Komentarz",
]
SALDO_HEADERS = [
    "Dostawca", "Jednostka", "Obszar", "Saldo_początkowe", "IN", "OUT", "Korekty",
    "Saldo_końcowe", "Saldo-2%", "Saldo-1%",
]


def _date_bounds(start: date | None, end: date | None) -> list:
    # Filter by the user-selected operation date (the report "Data").
    conditions = []
    if start is not None:
        conditions.append(Transaction.operation_date >= start)
    if end is not None:
        conditions.append(Transaction.operation_date <= end)
    return conditions


def _entity_filters(supplier_uuid, area_uuid, unit_uuid) -> list:
    conditions = []
    if supplier_uuid:
        conditions.append(Transaction.supplier_uuid == supplier_uuid)
    if area_uuid:
        conditions.append(Transaction.area_uuid == area_uuid)
    if unit_uuid:
        conditions.append(Transaction.unit_uuid == unit_uuid)
    return conditions


class ReportService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def booking_history(
        self,
        supplier_uuid: UUID | None = None,
        unit_uuid: UUID | None = None,
        area_uuid: UUID | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> tuple[str, list[str], list[list]]:
        t = Transaction
        query = (
            select(
                t.created_at, t.operation_date, User.username, Supplier.name, t.type,
                t.quantity, Unit.name, Area.name, t.comment,
            )
            .join(Supplier, t.supplier_uuid == Supplier.uuid)
            .join(Area, t.area_uuid == Area.uuid)
            .join(Unit, t.unit_uuid == Unit.uuid)
            .join(User, t.user_uuid == User.uuid)
            .where(*_entity_filters(supplier_uuid, area_uuid, unit_uuid), *_date_bounds(start, end))
            .order_by(t.created_at.desc())
        )

        result = await self.session.execute(query)

        rows = []
        for created_at, op_date, username, supplier, op_type, qty, unit, area, comment in result.all():
            rows.append([
                created_at,      # Data_dodania (auto)
                op_date,         # Data (user-selected)
                username,
                supplier,
                OPERATION_LABELS.get(op_type, op_type),
                qty,
                unit,
                area,
                comment,
            ])

        return "Raport", HISTORY_HEADERS, rows

    async def _aggregate_by_uuid(
        self, supplier_uuid, area_uuid, unit_uuid, start, end
    ) -> dict:
        t = Transaction
        in_sum = func.sum(case((t.type == TransactionType.RECEIPT.value, t.quantity), else_=0))
        out_sum = func.sum(case((t.type == TransactionType.ISSUE.value, t.quantity), else_=0))
        kor_sum = func.sum(case((t.type == TransactionType.CORRECTION.value, t.quantity), else_=0))

        query = (
            select(t.supplier_uuid, t.area_uuid, t.unit_uuid, in_sum, out_sum, kor_sum)
            .where(*_entity_filters(supplier_uuid, area_uuid, unit_uuid), *_date_bounds(start, end))
            .group_by(t.supplier_uuid, t.area_uuid, t.unit_uuid)
        )
        result = await self.session.execute(query)
        return {
            (r[0], r[1], r[2]): (int(r[3] or 0), int(r[4] or 0), int(r[5] or 0))
            for r in result.all()
        }

    async def saldo(
        self,
        supplier_uuid: UUID | None = None,
        unit_uuid: UUID | None = None,
        area_uuid: UUID | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> tuple[str, list[str], list[list]]:
        ranged = start is not None and end is not None
        agg = await self._aggregate_by_uuid(supplier_uuid, area_uuid, unit_uuid, start, end)

        # For a range, the opening balance = migrated opening + movements before the window.
        before = {}
        if ranged:
            before = await self._aggregate_by_uuid(
                supplier_uuid, area_uuid, unit_uuid, None, start - timedelta(days=1)
            )

        # Pallet rows give names, the migrated opening balance and the movements.
        query = (
            select(
                Pallet.supplier_uuid, Pallet.area_uuid, Pallet.unit_uuid,
                Pallet.quantity, Pallet.opening_balance,
                Supplier.name, Unit.name, Area.name,
            )
            .join(Supplier, Pallet.supplier_uuid == Supplier.uuid)
            .join(Unit, Pallet.unit_uuid == Unit.uuid)
            .join(Area, Pallet.area_uuid == Area.uuid)
            .order_by(Supplier.name)
        )
        if supplier_uuid:
            query = query.where(Pallet.supplier_uuid == supplier_uuid)
        if area_uuid:
            query = query.where(Pallet.area_uuid == area_uuid)
        if unit_uuid:
            query = query.where(Pallet.unit_uuid == unit_uuid)

        result = await self.session.execute(query)

        rows = []
        for s_uuid, a_uuid, u_uuid, quantity, opening, supplier, unit, area in result.all():
            in_, out, kor = agg.get((s_uuid, a_uuid, u_uuid), (0, 0, 0))
            # Receipts lower the balance, issues and corrections raise it.
            if ranged:
                b_in, b_out, b_kor = before.get((s_uuid, a_uuid, u_uuid), (0, 0, 0))
                saldo_start = opening + (b_out - b_in + b_kor)
                saldo_end = saldo_start + (out - in_ + kor)
            else:
                saldo_start = opening
                saldo_end = opening + quantity

            rows.append([
                supplier, unit, area, saldo_start, in_, out, kor,
                saldo_end, round(saldo_end * 0.98), round(saldo_end * 0.99),
            ])

        sheet = "Saldo_zakres" if ranged else "Saldo"
        return sheet, SALDO_HEADERS, rows
