from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin


class Area(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "areas"

    name = Column(String(100), nullable=False, unique=True)

    description = Column(String(255))

    pallets = relationship(
        "Pallet",
        back_populates="area",
    )

    transactions = relationship(
        "Transaction",
        back_populates="area",
    )