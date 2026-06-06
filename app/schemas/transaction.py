from uuid import UUID

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    type: str

    supplier_uuid: UUID
    area_uuid: UUID
    unit_uuid: UUID

    quantity: int
    comment: str | None = None


class TransactionResponse(BaseModel):
    uuid: UUID

    type: str

    supplier_uuid: UUID
    area_uuid: UUID
    unit_uuid: UUID
    user_uuid: UUID

    quantity: int
    comment: str | None

    model_config = {
        "from_attributes": True
    }