from uuid import UUID

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str


class SupplierUpdate(BaseModel):
    name: str


class SupplierResponse(BaseModel):
    uuid: UUID
    name: str

    model_config = {
        "from_attributes": True
    }
