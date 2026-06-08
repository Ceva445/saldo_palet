from uuid import UUID

from pydantic import BaseModel


class PalletResponse(BaseModel):
    uuid: UUID

    supplier_uuid: UUID
    area_uuid: UUID
    unit_uuid: UUID

    supplier_name: str
    area_name: str
    unit_name: str

    quantity: int

    model_config = {
        "from_attributes": True
    }
