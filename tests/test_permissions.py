# tests/test_permissions.py
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.jwt import create_access_token
from app.core.security import hash_password
from app.database.session import get_session
from app.dependencies import get_current_user
from app.main import app
from app.models.role import Role
from app.models.user import User
from app.repositories.area_repo import AreaRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.unit_repo import UnitRepository


def make_user(role: str):
    return type(
        "U",
        (),
        {
            "uuid": uuid4(),
            "username": "u",
            "is_active": True,
            "role": type("R", (), {"uuid": uuid4(), "name": role})(),
        },
    )()


def as_role(role: str):
    app.dependency_overrides[get_current_user] = lambda: make_user(role)


class TestApiPermissions:
    """API-level enforcement: role decides which modules are writable."""

    @pytest.mark.asyncio
    async def test_operator_can_write_masterdata(self, client):
        as_role("operator")
        res = await client.post("/areas", json={"name": f"Op {uuid4().hex[:6]}"})
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_viewer_cannot_write_masterdata(self, client):
        as_role("viewer")
        res = await client.post("/areas", json={"name": "Blocked"})
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_receipt(self, client):
        as_role("viewer")
        res = await client.post(
            "/transactions",
            json={
                "type": "RECEIPT",
                "supplier_uuid": str(uuid4()),
                "area_uuid": str(uuid4()),
                "unit_uuid": str(uuid4()),
                "quantity": 5,
            },
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_can_create_receipt(self, client, session):
        supplier = await SupplierRepository(session).create_one({"name": f"S {uuid4().hex[:6]}"})
        area = await AreaRepository(session).create_one({"name": f"A {uuid4().hex[:6]}"})
        unit = await UnitRepository(session).create_one({"name": f"U {uuid4().hex[:6]}"})
        await session.commit()

        as_role("operator")
        res = await client.post(
            "/transactions",
            json={
                "type": "RECEIPT",
                "supplier_uuid": str(supplier.uuid),
                "area_uuid": str(area.uuid),
                "unit_uuid": str(unit.uuid),
                "quantity": 5,
            },
        )
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


class TestRealAuthFlow:
    """Exercises the real get_current_user (DB read) + a write in one request,
    guarding against the 'transaction already begun' regression."""

    @pytest.mark.asyncio
    async def test_masterdata_write_with_real_token(self, session):
        role = Role(name="admin", description="x")
        session.add(role)
        await session.flush()
        user = User(
            username=f"real_{uuid4().hex[:6]}",
            hashed_password=hash_password("x"),
            role_uuid=role.uuid,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        await session.commit()

        token = create_access_token({"sub": str(user.uuid)})

        async def override_get_session():
            yield session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides.pop(get_current_user, None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post(
                    "/areas",
                    json={"name": f"Real {uuid4().hex[:6]}"},
                    headers={"Authorization": f"Bearer {token}"},
                )
            assert res.status_code == 200, res.text
        finally:
            app.dependency_overrides.clear()
