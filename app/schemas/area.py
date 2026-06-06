from uuid import UUID

from pydantic import BaseModel


class AreaCreate(BaseModel):
    name: str
    description: str | None = None


class AreaUpdate(BaseModel):
    name: str
    description: str | None = None


class AreaResponse(BaseModel):
    uuid: UUID
    name: str
    description: str | None

    model_config = {
        "from_attributes": True
    }
