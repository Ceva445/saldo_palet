# tests/test_reports.py
from io import BytesIO
from uuid import uuid4

import pytest
from openpyxl import load_workbook

from app.dependencies import get_current_user
from app.main import app
from app.repositories.area_repo import AreaRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.unit_repo import UnitRepository
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.services.transaction_service import TransactionService

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def make_user(role: str):
    return type(
        "U", (), {
            "uuid": uuid4(), "username": "u", "is_active": True,
            "role": type("R", (), {"uuid": uuid4(), "name": role})(),
        },
    )()


async def _seed(session):
    supplier = await SupplierRepository(session).create_one({"name": f"Sup {uuid4().hex[:6]}"})
    area = await AreaRepository(session).create_one({"name": f"Area {uuid4().hex[:6]}"})
    unit = await UnitRepository(session).create_one({"name": f"U {uuid4().hex[:6]}"})
    role = await RoleRepository(session).create_one({"name": f"r{uuid4().hex[:6]}"})
    user = await UserRepository(session).create_one(
        {"username": f"emp{uuid4().hex[:6]}", "hashed_password": "x", "role_uuid": role.uuid}
    )

    svc = TransactionService(session)
    base = {"supplier_uuid": supplier.uuid, "area_uuid": area.uuid, "unit_uuid": unit.uuid}
    await svc.create_transaction({**base, "type": "RECEIPT", "quantity": 10, "comment": None}, user.uuid)
    await svc.create_transaction({**base, "type": "ISSUE", "quantity": 3, "comment": None}, user.uuid)
    await session.commit()
    return supplier, area, unit


class TestReportsAPI:
    @pytest.mark.asyncio
    async def test_saldo_xlsx(self, client, session):
        await _seed(session)

        res = await client.get("/reports/saldo")
        assert res.status_code == 200
        assert res.headers["content-type"] == XLSX_MIME

        ws = load_workbook(BytesIO(res.content)).active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("Dostawca", "Jednostka", "Obszar", "IN", "OUT",
                           "Korekty", "Saldo", "Saldo-2%", "Saldo-1%")
        data = rows[1]
        assert data[3] == 10  # IN
        assert data[4] == 3   # OUT
        assert data[6] == 7   # Saldo (current stock)

    @pytest.mark.asyncio
    async def test_ksiegowania_xlsx(self, client, session):
        await _seed(session)

        res = await client.get("/reports/ksiegowania")
        assert res.status_code == 200
        assert res.headers["content-type"] == XLSX_MIME

        ws = load_workbook(BytesIO(res.content)).active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0][0] == "Data_dodania"
        # two transactions seeded
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_reports_require_permission(self, client):
        app.dependency_overrides[get_current_user] = lambda: make_user("nobody")
        res = await client.get("/reports/saldo")
        assert res.status_code == 403
