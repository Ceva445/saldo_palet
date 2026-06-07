# tests/test_services.py
import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy import text

from app.services.area_service import AreaService
from app.services.supplier_service import SupplierService
from app.services.unit_service import UnitService
from app.services.pallet_service import PalletService
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
from app.services.transaction_service import TransactionService
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.area_repo import AreaRepository
from app.repositories.unit_repo import UnitRepository
from app.repositories.pallet_repo import PalletRepository
from app.core.security import hash_password


class TestAreaService:
    """Tests for AreaService."""

    @pytest.mark.asyncio
    async def test_create_and_get_area(self, session):
        service = AreaService(session)
        
        area = await service.create({
            "name": f"Service Area {uuid4().hex[:8]}",
            "description": "Service Description"
        })
        
        assert area.name.startswith("Service Area")
        
        fetched = await service.get(area.uuid)
        assert fetched.uuid == area.uuid

    @pytest.mark.asyncio
    async def test_get_all_areas(self, session):
        service = AreaService(session)
        
        await service.create({"name": f"Area A {uuid4().hex[:8]}"})
        await service.create({"name": f"Area B {uuid4().hex[:8]}"})
        
        areas = await service.get_all()
        
        assert len(areas) == 2

    @pytest.mark.asyncio
    async def test_update_area(self, session):
        service = AreaService(session)
        
        original_name = f"Old Name {uuid4().hex[:8]}"
        new_name = f"New Name {uuid4().hex[:8]}"
        
        area = await service.create({"name": original_name})
        
        updated = await service.update(area.uuid, {"name": new_name})
        
        assert updated.name == new_name
        assert updated.name != original_name

    @pytest.mark.asyncio
    async def test_delete_area(self, session):
        service = AreaService(session)
        
        area = await service.create({"name": f"To Delete {uuid4().hex[:8]}"})
        
        await service.delete(area.uuid)
        
        result = await service.get(area.uuid)
        assert result is None  # Перевіряємо що об'єкт видалено


class TestSupplierService:
    """Tests for SupplierService."""

    @pytest.mark.asyncio
    async def test_create_supplier(self, session):
        service = SupplierService(session)
        
        supplier = await service.create({"name": f"Service Supplier {uuid4().hex[:8]}"})
        
        assert supplier.name.startswith("Service Supplier")

    @pytest.mark.asyncio
    async def test_update_supplier(self, session):
        service = SupplierService(session)
        
        original_name = f"Original Name {uuid4().hex[:8]}"
        new_name = f"Updated Name {uuid4().hex[:8]}"
        
        supplier = await service.create({"name": original_name})
        
        updated = await service.update(supplier.uuid, {"name": new_name})
        
        assert updated.name == new_name
        assert updated.name != original_name

    @pytest.mark.asyncio
    async def test_delete_supplier(self, session):
        service = SupplierService(session)
        
        supplier = await service.create({"name": f"Temporary {uuid4().hex[:8]}"})
        
        await service.delete(supplier.uuid)
        
        result = await service.get(supplier.uuid)
        assert result is None


class TestUnitService:
    """Tests for UnitService."""

    @pytest.mark.asyncio
    async def test_crud_operations(self, session):
        service = UnitService(session)
        
        # Create
        unit = await service.create({"name": f"szt_{uuid4().hex[:8]}"})
        assert unit.name.startswith("szt_")
        
        # Get
        fetched = await service.get(unit.uuid)
        assert fetched.name == unit.name
        
        # Update
        updated = await service.update(unit.uuid, {"name": f"kg_{uuid4().hex[:8]}"})
        assert updated.name.startswith("kg_")
        
        # Delete
        await service.delete(unit.uuid)
        result = await service.get(unit.uuid)
        assert result is None


class TestAuthService:
    """Tests for AuthService."""

    @pytest_asyncio.fixture
    async def setup_user(self, session):
        """Create a test user."""
        role_uuid = str(uuid4())  # Конвертуємо в рядок
        
        await session.execute(
            text("INSERT INTO roles (uuid, name) VALUES (:uuid, :name)"),
            {"uuid": role_uuid, "name": "admin"}
        )
        
        user_uuid = str(uuid4())
        password_hash = hash_password("testpassword")
        
        await session.execute(
            text("""
                INSERT INTO users (uuid, username, hashed_password, role_uuid, is_active) 
                VALUES (:uuid, :username, :password, :role_uuid, :is_active)
            """),
            {
                "uuid": user_uuid,
                "username": "testuser",
                "password": password_hash,
                "role_uuid": role_uuid,
                "is_active": True
            }
        )
        await session.commit()
        
        return {"uuid": user_uuid, "username": "testuser", "password": "testpassword"}

    @pytest.mark.asyncio
    async def test_login_success(self, session, setup_user):
        service = AuthService(session)
        
        result = await service.login("testuser", "testpassword")
        
        assert result is not None
        assert "access_token" in result
        assert result["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, session, setup_user):
        service = AuthService(session)
        
        result = await service.login("testuser", "wrongpassword")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, session, setup_user):
        service = AuthService(session)
        
        result = await service.login("nonexistent", "testpassword")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_register_user(self, session):
        import uuid as uuid_module
        
        service = AuthService(session)
        
        role_uuid_str = str(uuid4())
        await session.execute(
            text("INSERT INTO roles (uuid, name) VALUES (:uuid, :name)"),
            {"uuid": role_uuid_str, "name": "operator"}
        )
        await session.commit()
        
        # Конвертуємо рядок назад в UUID
        role_uuid = uuid_module.UUID(role_uuid_str)
        
        user = await service.register("newuser", "password123", role_uuid)
        
        assert user.username == "newuser"
        assert user.hashed_password != "password123"


class TestPermissionService:
    """Tests for PermissionService."""

    def test_admin_has_all_permissions(self):
        service = PermissionService()
        
        assert service.has_access("admin", "receipts") is True
        assert service.has_access("admin", "releases") is True
        assert service.has_access("admin", "reports") is True
        assert service.has_access("admin", "masterdata") is True
        assert service.has_access("admin", "corrections") is True

    def test_operator_permissions(self):
        service = PermissionService()
        
        assert service.has_access("operator", "receipts") is True
        assert service.has_access("operator", "releases") is True
        assert service.has_access("operator", "reports") is True
        assert service.has_access("operator", "masterdata") is False

    def test_viewer_permissions(self):
        service = PermissionService()
        
        assert service.has_access("viewer", "reports") is True
        assert service.has_access("viewer", "receipts") is False


class TestTransactionService:
    """Tests for TransactionService."""

    @pytest_asyncio.fixture
    async def setup_data(self, session):
        """Setup test data for transactions."""
        import uuid as uuid_module
        
        supplier_repo = SupplierRepository(session)
        area_repo = AreaRepository(session)
        unit_repo = UnitRepository(session)
        
        supplier = await supplier_repo.create_one({"name": f"Test Supplier {uuid4().hex[:8]}"})
        area = await area_repo.create_one({"name": f"Test Area {uuid4().hex[:8]}"})
        unit = await unit_repo.create_one({"name": f"szt_{uuid4().hex[:8]}"})
        
        # Create user with string UUIDs for raw SQL
        role_uuid_str = str(uuid4())
        user_uuid_str = str(uuid4())
        
        await session.execute(
            text("INSERT INTO roles (uuid, name) VALUES (:uuid, :name)"),
            {"uuid": role_uuid_str, "name": "admin"}
        )
        await session.execute(
            text("""
                INSERT INTO users (uuid, username, hashed_password, role_uuid) 
                VALUES (:uuid, :username, :password, :role_uuid)
            """),
            {
                "uuid": user_uuid_str,
                "username": "testuser",
                "password": "hash",
                "role_uuid": role_uuid_str
            }
        )
        await session.commit()
        
        # Convert to proper UUID objects
        user_uuid = uuid_module.UUID(user_uuid_str)
        
        return {
            "supplier_uuid": supplier.uuid,
            "area_uuid": area.uuid,
            "unit_uuid": unit.uuid,
            "user_uuid": user_uuid,  # Тепер це UUID, не рядок
        }

    @pytest.mark.asyncio
    async def test_create_receipt_transaction(self, session, setup_data):
        service = TransactionService(session)
        
        result = await service.create_transaction({
            "type": "RECEIPT",
            "supplier_uuid": setup_data["supplier_uuid"],
            "area_uuid": setup_data["area_uuid"],
            "unit_uuid": setup_data["unit_uuid"],
            "quantity": 10,
            "comment": "Test receipt"
        }, setup_data["user_uuid"])
        
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_issue_insufficient_stock(self, session, setup_data):
        service = TransactionService(session)
        
        pallet_repo = PalletRepository(session)
        await pallet_repo.create_one({
            "supplier_uuid": setup_data["supplier_uuid"],
            "area_uuid": setup_data["area_uuid"],
            "quantity": 5
        })
        
        with pytest.raises(Exception) as exc_info:
            await service.create_transaction({
                "type": "ISSUE",
                "supplier_uuid": setup_data["supplier_uuid"],
                "area_uuid": setup_data["area_uuid"],
                "unit_uuid": setup_data["unit_uuid"],
                "quantity": 10,
                "comment": None
            }, setup_data["user_uuid"])
        
        assert "Not enough stock" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_correction_transaction(self, session, setup_data):
        service = TransactionService(session)
        
        pallet_repo = PalletRepository(session)
        await pallet_repo.create_one({
            "supplier_uuid": setup_data["supplier_uuid"],
            "area_uuid": setup_data["area_uuid"],
            "quantity": 100
        })
        
        result = await service.create_transaction({
            "type": "CORRECTION",
            "supplier_uuid": setup_data["supplier_uuid"],
            "area_uuid": setup_data["area_uuid"],
            "unit_uuid": setup_data["unit_uuid"],
            "quantity": 42,
            "comment": "Correction"
        }, setup_data["user_uuid"])
        
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_invalid_transaction_type(self, session, setup_data):
        service = TransactionService(session)
        
        with pytest.raises(Exception) as exc_info:
            await service.create_transaction({
                "type": "INVALID",
                "supplier_uuid": setup_data["supplier_uuid"],
                "area_uuid": setup_data["area_uuid"],
                "unit_uuid": setup_data["unit_uuid"],
                "quantity": 10,
                "comment": None
            }, setup_data["user_uuid"])
        
        assert "Invalid transaction type" in str(exc_info.value)