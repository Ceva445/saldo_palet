# tests/test_users.py
from uuid import uuid4

import pytest

from app.dependencies import get_current_user
from app.main import app
from app.repositories.role_repo import RoleRepository


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


class TestUsersAPI:
    @pytest.mark.asyncio
    async def test_admin_creates_and_lists_user(self, client, session):
        await RoleRepository(session).create_one({"name": "operator", "description": "x"})
        await session.commit()

        res = await client.post(
            "/users",
            json={"username": "jan", "password": "secret", "role": "operator"},
        )
        assert res.status_code == 200, res.text
        assert res.json()["username"] == "jan"
        assert res.json()["role"] == "operator"

        listed = await client.get("/users")
        assert any(u["username"] == "jan" for u in listed.json())

    @pytest.mark.asyncio
    async def test_create_user_unknown_role(self, client, session):
        res = await client.post(
            "/users",
            json={"username": "x", "password": "p", "role": "ghost"},
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_admin_updates_user(self, client, session):
        await RoleRepository(session).create_one({"name": "operator", "description": "x"})
        await RoleRepository(session).create_one({"name": "admin", "description": "x"})
        await session.commit()

        created = await client.post(
            "/users",
            json={"username": "jan", "password": "secret", "role": "operator"},
        )
        uuid = created.json()["uuid"]

        res = await client.put(
            f"/users/{uuid}",
            json={"username": "jan2", "role": "admin", "password": "newpass"},
        )
        assert res.status_code == 200, res.text
        assert res.json()["username"] == "jan2"
        assert res.json()["role"] == "admin"

    @pytest.mark.asyncio
    async def test_admin_deletes_user(self, client, session):
        await RoleRepository(session).create_one({"name": "operator", "description": "x"})
        await session.commit()

        created = await client.post(
            "/users",
            json={"username": "temp", "password": "p", "role": "operator"},
        )
        uuid = created.json()["uuid"]

        res = await client.delete(f"/users/{uuid}")
        assert res.status_code == 200
        assert res.json() == {"success": True}

        listed = await client.get("/users")
        assert all(u["username"] != "temp" for u in listed.json())

    @pytest.mark.asyncio
    async def test_cannot_delete_self(self, client):
        me = (await client.get("/auth/me")).json()
        res = await client.delete(f"/users/{me['uuid']}")
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_manage_users(self, client):
        app.dependency_overrides[get_current_user] = lambda: make_user("operator")
        res = await client.post(
            "/users",
            json={"username": "x", "password": "p", "role": "operator"},
        )
        assert res.status_code == 403

        res2 = await client.get("/users")
        assert res2.status_code == 403

        res3 = await client.put(f"/users/{uuid4()}", json={"username": "y"})
        assert res3.status_code == 403

        res4 = await client.delete(f"/users/{uuid4()}")
        assert res4.status_code == 403
