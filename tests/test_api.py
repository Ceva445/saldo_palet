# tests/test_api.py
import pytest
from uuid import uuid4
from sqlalchemy import text

from app.core.security import hash_password
from app.repositories.area_repo import AreaRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.unit_repo import UnitRepository


class TestAuthAPI:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, client, session):
        """Test successful login."""
        role_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        await session.execute(
            text("INSERT INTO roles (uuid, name) VALUES (:uuid, :name)"),
            {"uuid": role_uuid, "name": "admin"}
        )
        await session.execute(
            text("""
                INSERT INTO users (uuid, username, hashed_password, role_uuid, is_active) 
                VALUES (:uuid, :username, :password, :role_uuid, :is_active)
            """),
            {
                "uuid": user_uuid,
                "username": "testuser",
                "password": hash_password("testpass"),
                "role_uuid": role_uuid,
                "is_active": True
            }
        )
        await session.commit()
        
        response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, session):
        """Test login with invalid credentials."""
        role_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        await session.execute(
            text("INSERT INTO roles (uuid, name) VALUES (:uuid, :name)"),
            {"uuid": role_uuid, "name": "admin"}
        )
        await session.execute(
            text("""
                INSERT INTO users (uuid, username, hashed_password, role_uuid) 
                VALUES (:uuid, :username, :password, :role_uuid)
            """),
            {
                "uuid": user_uuid,
                "username": "testuser",
                "password": hash_password("testpass"),
                "role_uuid": role_uuid
            }
        )
        await session.commit()
        
        response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "wrongpass"
        })
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAreaAPI:
    """Tests for area endpoints."""

    @pytest.mark.asyncio
    async def test_create_area(self, client):
        """Test creating a new area."""
        response = await client.post("/areas", json={
            "name": f"Test Area {uuid4().hex[:8]}",
            "description": "Test Description"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"].startswith("Test Area")

    @pytest.mark.asyncio
    async def test_get_areas(self, client, session):
        """Test getting all areas."""
        area_repo = AreaRepository(session)
        await area_repo.create_one({"name": f"Area 1 {uuid4().hex[:8]}"})
        await area_repo.create_one({"name": f"Area 2 {uuid4().hex[:8]}"})
        await session.commit()
        
        response = await client.get("/areas")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_area_by_uuid(self, client, session):
        """Test getting area by UUID."""
        area_repo = AreaRepository(session)
        area = await area_repo.create_one({"name": f"Specific Area {uuid4().hex[:8]}"})
        await session.commit()
        
        response = await client.get(f"/areas/{area.uuid}")
        
        assert response.status_code == 200
        assert response.json()["name"] == area.name

    @pytest.mark.asyncio
    async def test_update_area(self, client, session):
        """Test updating an area."""
        area_repo = AreaRepository(session)
        area = await area_repo.create_one({"name": f"Old Name {uuid4().hex[:8]}"})
        await session.commit()
        
        new_name = f"New Name {uuid4().hex[:8]}"
        response = await client.put(f"/areas/{area.uuid}", json={
            "name": new_name,
            "description": "Updated Description"
        })
        
        assert response.status_code == 200
        assert response.json()["name"] == new_name

    @pytest.mark.asyncio
    async def test_delete_area(self, client, session):
        """Test deleting an area."""
        area_repo = AreaRepository(session)
        area = await area_repo.create_one({"name": f"To Delete {uuid4().hex[:8]}"})
        await session.commit()
        
        response = await client.delete(f"/areas/{area.uuid}")
        
        assert response.status_code == 200
        assert response.json() == {"success": True}


class TestSupplierAPI:
    """Tests for supplier endpoints."""

    @pytest.mark.asyncio
    async def test_create_supplier(self, client):
        """Test creating a supplier."""
        response = await client.post("/suppliers", json={
            "name": f"Test Supplier {uuid4().hex[:8]}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"].startswith("Test Supplier")

    @pytest.mark.asyncio
    async def test_get_suppliers(self, client, session):
        """Test getting all suppliers."""
        supplier_repo = SupplierRepository(session)
        await supplier_repo.create_one({"name": f"Supplier 1 {uuid4().hex[:8]}"})
        await supplier_repo.create_one({"name": f"Supplier 2 {uuid4().hex[:8]}"})
        await session.commit()
        
        response = await client.get("/suppliers")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestSearchPagination:
    """Server-side search + pagination for masterdata lists."""

    @pytest.mark.asyncio
    async def test_search_and_paginate_areas(self, client, session):
        repo = AreaRepository(session)
        for i in range(5):
            await repo.create_one({"name": f"Strefa {i}"})
        await repo.create_one({"name": "Inne"})
        await session.commit()

        # First page of the "Strefa" matches.
        res = await client.get("/areas?search=Strefa&limit=2&offset=0")
        assert res.status_code == 200
        assert len(res.json()) == 2
        assert res.headers["X-Total-Count"] == "5"

        # Offset returns the remainder.
        res2 = await client.get("/areas?search=Strefa&limit=2&offset=4")
        assert len(res2.json()) == 1

    @pytest.mark.asyncio
    async def test_list_without_params_returns_all(self, client, session):
        repo = AreaRepository(session)
        await repo.create_one({"name": f"A {uuid4().hex[:6]}"})
        await repo.create_one({"name": f"B {uuid4().hex[:6]}"})
        await session.commit()

        res = await client.get("/areas")
        assert res.status_code == 200
        assert len(res.json()) == 2


class TestUnitAPI:
    """Tests for unit endpoints."""

    @pytest.mark.asyncio
    async def test_create_unit(self, client):
        """Test creating a unit."""
        response = await client.post("/units", json={
            "name": f"szt_{uuid4().hex[:8]}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"].startswith("szt_")

    @pytest.mark.asyncio
    async def test_get_units(self, client, session):
        """Test getting all units."""
        unit_repo = UnitRepository(session)
        await unit_repo.create_one({"name": f"kg_{uuid4().hex[:8]}"})
        await unit_repo.create_one({"name": f"l_{uuid4().hex[:8]}"})
        await session.commit()
        
        response = await client.get("/units")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2