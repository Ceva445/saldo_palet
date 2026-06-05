from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin


class Supplier(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "suppliers"

    name = Column(String(255), nullable=False, unique=True)

    pallets = relationship(
        "Pallet",
        back_populates="supplier",
    )

    transactions = relationship(
        "Transaction",
        back_populates="supplier",
    )