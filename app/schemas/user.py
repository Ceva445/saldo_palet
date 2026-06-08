from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


class UserOut(BaseModel):
    uuid: UUID
    username: str
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class RoleOut(BaseModel):
    uuid: UUID
    name: str
    description: str | None = None

    model_config = {
        "from_attributes": True
    }
