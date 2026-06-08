from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: 'UserResponse'


class UserResponse(BaseModel):
    uuid: UUID
    username: str
    is_active: bool
    role: str
    permissions: list[str] = []

    model_config = {
        "from_attributes": True
    }

class UserCreate(BaseModel):
    username: str
    role: str


class UserModel(UserCreate):
    pass