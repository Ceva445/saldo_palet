# tests/test_repositories.py
import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy import text

from app.repositories.area_repo import AreaRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.unit_repo import UnitRepository
from app.repositories.pallet_repo import PalletRepository
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository


class TestAreaRepository:
    """Tests for AreaRepository."""

    @pytest.mark.asyncio
    async def test_create_area(self, session):
        repo = AreaRepository(session)
        
        data = {
            "name": f"Test Area {uuid4().hex[:8]}",  # Унікальне ім'я
            "description": "Test Description"
        }
        
        area = await repo.create_one(data)
        
        assert area.name == data["name"]
        assert area.description == "Test Description"
        assert area.uuid is not None

    @pytest.mark.asyncio
    async def test_get_area_by_name(self, session):
        repo = AreaRepository(session)
        
        unique_name = f"Unique Area {uuid4().hex[:8]}"
        data = {"name": unique_name}
        await repo.create_one(data)
        
        area = await repo.get_by_name(unique_name)
        
        assert area is not None
        assert area.name == unique_name

    @pytest.mark.asyncio
    async def test_get_area_not_found(self, session):
        repo = AreaRepository(session)
        
        area = await repo.get_by_name("Non-existent Area")
        
        assert area is None

    @pytest.mark.asyncio
    async def test_get_all_areas(self, session):
        repo = AreaRepository(session)
        
        await repo.create_one({"name": f"Area 1 {uuid4().hex[:8]}"})
        await repo.create_one({"name": f"Area 2 {uuid4().hex[:8]}"})
        
        areas = await repo.get_all()
        
        assert len(areas) == 2

    @pytest.mark.asyncio
    async def test_update_area(self, session):
        repo = AreaRepository(session)
        
        original_name = f"Original Area {uuid4().hex[:8]}"
        new_name = f"Updated Area {uuid4().hex[:8]}"
        
        area = await repo.create_one({"name": original_name})
        
        updated = await repo.update_one(area.uuid, {"name": new_name})
        
        assert updated.name == new_name
        assert updated.name != original_name

    @pytest.mark.asyncio
    async def test_delete_area(self, session):
        repo = AreaRepository(session)
        
        area = await repo.create_one({"name": f"To Delete {uuid4().hex[:8]}"})
        
        deleted = await repo.delete_one(area.uuid)
        
        assert deleted.name == area.name
        
        # Verify deletion
        result = await repo.get_one(uuid=area.uuid)
        assert result is None


class TestSupplierRepository:
    """Tests for SupplierRepository."""

    @pytest.mark.asyncio
    async def test_create_supplier(self, session):
        repo = SupplierRepository(session)
        
        unique_name = f"Test Supplier {uuid4().hex[:8]}"
        supplier = await repo.create_one({"name": unique_name})
        
        assert supplier.name == unique_name
        assert supplier.uuid is not None

    @pytest.mark.asyncio
    async def test_get_supplier_by_name(self, session):
        repo = SupplierRepository(session)
        
        unique_name = f"Unique Supplier {uuid4().hex[:8]}"
        await repo.create_one({"name": unique_name})
        
        supplier = await repo.get_by_name(unique_name)
        
        assert supplier is not None
        assert supplier.name == unique_name

    @pytest.mark.asyncio
    async def test_get_many_suppliers(self, session):
        repo = SupplierRepository(session)
        
        await repo.create_one({"name": f"Supplier A {uuid4().hex[:8]}"})
        await repo.create_one({"name": f"Supplier B {uuid4().hex[:8]}"})
        
        suppliers, total = await repo.get_many(page=1, limit=10)
        
        assert len(suppliers) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_pagination(self, session):
        repo = SupplierRepository(session)
        
        for i in range(5):
            await repo.create_one({"name": f"Supplier {i} {uuid4().hex[:8]}"})
        
        suppliers_page1, total = await repo.get_many(page=1, limit=2)
        suppliers_page2, _ = await repo.get_many(page=2, limit=2)
        
        assert len(suppliers_page1) == 2
        assert len(suppliers_page2) == 2
        assert total == 5

    @pytest.mark.asyncio
    async def test_delete_many(self, session):
        repo = SupplierRepository(session)
        
        name_to_delete = f"Delete 1 {uuid4().hex[:8]}"
        await repo.create_one({"name": name_to_delete})
        await repo.create_one({"name": f"Delete 2 {uuid4().hex[:8]}"})
        
        await repo.delete_many(name=name_to_delete)
        
        suppliers, _ = await repo.get_many(limit=10)
        assert len(suppliers) == 1


class TestUnitRepository:
    """Tests for UnitRepository."""

    @pytest.mark.asyncio
    async def test_create_unit(self, session):
        repo = UnitRepository(session)
        
        unit = await repo.create_one({"name": f"szt_{uuid4().hex[:8]}"})
        
        assert unit.name.startswith("szt_")

    @pytest.mark.asyncio
    async def test_get_by_name(self, session):
        repo = UnitRepository(session)
        
        unique_name = f"kg_{uuid4().hex[:8]}"
        await repo.create_one({"name": unique_name})
        
        unit = await repo.get_by_name(unique_name)
        
        assert unit is not None
        assert unit.name == unique_name

    @pytest.mark.asyncio
    async def test_list_all_by_ids(self, session):
        repo = UnitRepository(session)
        
        unit1 = await repo.create_one({"name": f"m_{uuid4().hex[:8]}"})
        unit2 = await repo.create_one({"name": f"l_{uuid4().hex[:8]}"})
        await repo.create_one({"name": f"pcs_{uuid4().hex[:8]}"})
        
        units = await repo.list_all_by_ids([unit1.uuid, unit2.uuid])
        
        assert len(units) == 2


class TestPalletRepository:
    """Tests for PalletRepository."""

    @pytest_asyncio.fixture
    async def setup_pallet_data(self, session):
        """Create test data for pallet tests."""
        supplier_repo = SupplierRepository(session)
        area_repo = AreaRepository(session)
        
        supplier = await supplier_repo.create_one({"name": f"Test Supplier {uuid4().hex[:8]}"})
        area = await area_repo.create_one({"name": f"Test Area {uuid4().hex[:8]}"})
        
        return {
            "supplier_uuid": supplier.uuid,
            "area_uuid": area.uuid,
        }

    @pytest.mark.asyncio
    async def test_create_pallet(self, session, setup_pallet_data):
        repo = PalletRepository(session)
        
        pallet = await repo.create_one({
            **setup_pallet_data,
            "quantity": 100
        })
        
        assert pallet.quantity == 100
        assert pallet.supplier_uuid == setup_pallet_data["supplier_uuid"]
        assert pallet.area_uuid == setup_pallet_data["area_uuid"]

    @pytest.mark.asyncio
    async def test_get_stock(self, session, setup_pallet_data):
        repo = PalletRepository(session)
        
        await repo.create_one({
            **setup_pallet_data,
            "quantity": 50
        })
        
        stock = await repo.get_stock(
            setup_pallet_data["supplier_uuid"],
            setup_pallet_data["area_uuid"],
        )
        
        assert stock is not None
        assert stock.quantity == 50

    @pytest.mark.asyncio
    async def test_get_stock_not_found(self, session, setup_pallet_data):
        repo = PalletRepository(session)
        
        stock = await repo.get_stock(
            setup_pallet_data["supplier_uuid"],
            setup_pallet_data["area_uuid"],
        )
        
        assert stock is None

    @pytest.mark.asyncio
    async def test_unique_constraint(self, session, setup_pallet_data):
        repo = PalletRepository(session)
        
        await repo.create_one({
            **setup_pallet_data,
            "quantity": 100
        })
        
        # Should raise integrity error due to unique constraint
        with pytest.raises(Exception):
            await repo.create_one({
                **setup_pallet_data,
                "quantity": 200
            })


class TestTransactionRepository:
    """Tests for TransactionRepository."""

    @pytest_asyncio.fixture
    async def setup_transaction_data(self, session):
        """Create test data for transaction tests."""
        supplier_repo = SupplierRepository(session)
        area_repo = AreaRepository(session)
        unit_repo = UnitRepository(session)
        
        supplier = await supplier_repo.create_one({"name": f"Transaction Supplier {uuid4().hex[:8]}"})
        area = await area_repo.create_one({"name": f"Transaction Area {uuid4().hex[:8]}"})
        unit = await unit_repo.create_one({"name": f"szt_{uuid4().hex[:8]}"})
        
        # Create role and user using raw SQL з рядковими UUID
        role_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        await session.execute(
            text("INSERT INTO roles (uuid, name) VALUES (:uuid, :name)"),
            {"uuid": role_uuid, "name": "admin"}
        )
        
        await session.execute(
            text("INSERT INTO users (uuid, username, hashed_password, role_uuid) VALUES (:uuid, :username, :password, :role_uuid)"),
            {
                "uuid": user_uuid,
                "username": "testuser",
                "password": "hashedpass",
                "role_uuid": role_uuid
            }
        )
        await session.commit()
        
        return {
            "supplier_uuid": supplier.uuid,
            "area_uuid": area.uuid,
            "unit_uuid": unit.uuid,
            "user_uuid": uuid4(),
        }

    @pytest.mark.asyncio
    async def test_create_transaction(self, session, setup_transaction_data):
        repo = TransactionRepository(session)
        
        transaction = await repo.create_one({
            **setup_transaction_data,
            "type": "RECEIPT",
            "quantity": 10,
            "comment": "Test transaction"
        })
        
        assert transaction.type == "RECEIPT"
        assert transaction.quantity == 10

    @pytest.mark.asyncio
    async def test_get_by_period(self, session, setup_transaction_data):
        from datetime import datetime, timedelta, timezone
        
        repo = TransactionRepository(session)
        
        await repo.create_one({
            **setup_transaction_data,
            "type": "RECEIPT",
            "quantity": 100,
            "comment": None
        })
        
        # Використовуємо timezone-aware datetime
        date_from = datetime.now(timezone.utc) - timedelta(days=1)
        date_to = datetime.now(timezone.utc) + timedelta(days=1)
        
        transactions = await repo.get_by_period(date_from, date_to)
        
        assert len(transactions) == 1