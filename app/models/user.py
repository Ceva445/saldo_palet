from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin


class User(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username = Column(String(100), nullable=False, unique=True)

    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)

    role_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.uuid"),
        nullable=False,
    )

    role = relationship(
        "Role",
        back_populates="users",
    )

    transactions = relationship(
        "Transaction",
        back_populates="user",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
    )