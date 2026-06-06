from uuid import UUID

from pydantic import BaseModel


class PalletResponse(BaseModel):
    uuid: UUID

    supplier_uuid: UUID
    area_uuid: UUID

    quantity: int

    model_config = {
        "from_attributes": True
    }