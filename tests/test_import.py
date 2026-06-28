# tests/test_import.py
from datetime import date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models.area import Area
from app.models.supplier import Supplier
from app.models.transaction import Transaction
from app.models.unit import Unit
from app.models.user import User
from app.repositories.area_repo import AreaRepository
from app.repositories.pallet_repo import PalletRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.unit_repo import UnitRepository
from app.repositories.user_repo import UserRepository
from scripts._raport import Row
from scripts.import_transactions import run_import
from scripts.import_validate import run_validate
from scripts.import_opening_balances import run_import_opening
from scripts.recompute_pallets import recompute


def make_row(no, op, val, *, supplier="TUBADZIN", area="Stock", unit="EUR",
             user="ext_u", when=datetime(2025, 10, 22, 7, 10)):
    return Row(no, when, when.date(), user, supplier, op, val, unit, area, None)


class TestImportValidate:
    @pytest.mark.asyncio
    async def test_creates_masterdata_and_reports(self, session):
        rows = [
            make_row(2, "IN", -10),
            make_row(3, "OUT", 3),
            make_row(4, "IN", -5, area=""),  # invalid: empty Obszar
        ]
        report = await run_validate(session, rows)

        assert report["created"]["users"] == ["ext_u"]
        assert report["created"]["suppliers"] == ["TUBADZIN"]
        assert report["created"]["units"] == ["EUR"]
        assert report["created"]["areas"] == ["Stock"]
        assert report["valid_rows"] == 2
        assert len(report["errors"]) == 1

        from app.core.security import verify_password
        user = (await session.execute(select(User).where(User.username == "ext_u"))).scalar_one()
        assert user.must_change_password is True
        assert verify_password("123", user.hashed_password)


class TestImportTransactions:
    @pytest.mark.asyncio
    async def test_inserts_and_computes_balance(self, session):
        rows = [
            make_row(2, "IN", -10, when=datetime(2025, 10, 22, 7, 10)),
            make_row(3, "OUT", 3, when=datetime(2025, 10, 22, 8, 0)),
            make_row(4, "IN", -5, area=""),  # skipped (invalid)
        ]
        await run_validate(session, rows)
        result = await run_import(session, rows)

        assert result["inserted"] == 2
        assert result["skipped_invalid"] == 1

        count = (await session.execute(select(func.count()).select_from(Transaction))).scalar()
        assert count == 2

        supplier = (await session.execute(select(Supplier))).scalar_one()
        unit = (await session.execute(select(Unit))).scalar_one()
        area = (await session.execute(select(Area).where(Area.name == "Stock"))).scalar_one()
        pallet = await PalletRepository(session).get_stock(supplier.uuid, area.uuid, unit.uuid)
        assert pallet.quantity == -7  # IN 10 (owe), OUT 3 (returned) → -10 + 3

    @pytest.mark.asyncio
    async def test_correction_is_signed_delta(self, session):
        rows = [
            make_row(2, "IN", -10, when=datetime(2025, 10, 22, 7, 0)),
            make_row(3, "KOREKTA", -4, when=datetime(2025, 10, 22, 8, 0)),  # delta -4
        ]
        await run_validate(session, rows)
        await run_import(session, rows)

        supplier = (await session.execute(select(Supplier))).scalar_one()
        unit = (await session.execute(select(Unit))).scalar_one()
        area = (await session.execute(select(Area).where(Area.name == "Stock"))).scalar_one()
        pallet = await PalletRepository(session).get_stock(supplier.uuid, area.uuid, unit.uuid)
        assert pallet.quantity == -14  # IN 10 → -10, correction -4 → -14

    @pytest.mark.asyncio
    async def test_recompute_pallets_from_ledger(self, session):
        supplier = await SupplierRepository(session).create_one({"name": f"S {uuid4().hex[:6]}"})
        area = await AreaRepository(session).create_one({"name": "Stock"})
        unit = await UnitRepository(session).create_one({"name": f"U {uuid4().hex[:6]}"})
        role = await RoleRepository(session).create_one({"name": f"r{uuid4().hex[:6]}"})
        user = await UserRepository(session).create_one(
            {"username": f"e{uuid4().hex[:6]}", "hashed_password": "x", "role_uuid": role.uuid}
        )

        base = {"supplier_uuid": supplier.uuid, "area_uuid": area.uuid,
                "unit_uuid": unit.uuid, "user_uuid": user.uuid, "operation_date": date(2025, 10, 22)}
        tx_repo = TransactionRepository(session)
        await tx_repo.create_one({**base, "type": "RECEIPT", "quantity": 10})
        await tx_repo.create_one({**base, "type": "ISSUE", "quantity": 3})
        await session.commit()

        n = await recompute(session)
        assert n == 1

        pallet = await PalletRepository(session).get_stock(supplier.uuid, area.uuid, unit.uuid)
        assert pallet.quantity == -7  # -10 receipt + 3 issue

    @pytest.mark.asyncio
    async def test_import_opening_balances(self, session):
        # Script creates missing master data and sets opening_balance; zeros skipped.
        rows = [
            ("Amica", "EUR", "Stock", -50),
            ("Amica", "EUR", "Zwroty", 0),   # skipped (zero)
        ]
        result = await run_import_opening(session, rows)

        assert result["applied"] == 1
        assert result["skipped_zero"] == 1
        assert result["created_masterdata"]["suppliers"] == 1

        supplier = (await session.execute(select(Supplier).where(Supplier.name == "Amica"))).scalar_one()
        area = (await session.execute(select(Area).where(Area.name == "Stock"))).scalar_one()
        unit = (await session.execute(select(Unit).where(Unit.name == "EUR"))).scalar_one()
        pallet = await PalletRepository(session).get_stock(supplier.uuid, area.uuid, unit.uuid)
        assert pallet.opening_balance == -50

    @pytest.mark.asyncio
    async def test_refuses_second_run_without_force(self, session):
        rows = [make_row(2, "IN", -1)]
        await run_validate(session, rows)
        await run_import(session, rows)

        with pytest.raises(SystemExit):
            await run_import(session, rows)
