from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin


class Unit(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "units"

    name = Column(
        String(100), 
        nullable=False,
        unique=True,)

    transactions = relationship(
        "Transaction",
        back_populates="unit",
    )