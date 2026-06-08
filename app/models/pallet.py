from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin


class Pallet(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "pallets"

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

    quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    supplier = relationship(
        "Supplier",
        back_populates="pallets",
    )

    area = relationship(
        "Area",
        back_populates="pallets",
    )

    unit = relationship(
        "Unit",
        back_populates="pallets",
    )

    __table_args__ = (
        UniqueConstraint(
            "supplier_uuid",
            "area_uuid",
            "unit_uuid",
            name="uq_supplier_area_unit",
        ),
    )
