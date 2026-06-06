from sqlalchemy import Column, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin

from enum import Enum

class TransactionType(str, Enum):
    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    CORRECTION = "CORRECTION"


class Transaction(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "transactions"

    type = Column(
        SQLEnum(TransactionType),
        nullable=False,
    )

    supplier_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.uuid"),
        nullable=False,
    )

    area_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("areas.uuid"),
        nullable=False,
    )

    unit_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("units.uuid"),
        nullable=False,
    )

    user_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
    )

    comment = Column(Text)

    supplier = relationship(
        "Supplier",
        back_populates="transactions",
    )

    area = relationship(
        "Area",
        back_populates="transactions",
    )

    unit = relationship(
        "Unit",
        back_populates="transactions",
    )

    user = relationship(
        "User",
        back_populates="transactions",
    )