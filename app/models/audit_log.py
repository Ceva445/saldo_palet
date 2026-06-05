from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin, UUIDMixin


class AuditLog(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    user_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=False,
    )

    action = Column(
        String(100),
        nullable=False,
    )

    entity_name = Column(
        String(100),
        nullable=False,
    )

    entity_uuid = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    old_data = Column(JSON)

    new_data = Column(JSON)

    user = relationship(
        "User",
        back_populates="audit_logs",
    )