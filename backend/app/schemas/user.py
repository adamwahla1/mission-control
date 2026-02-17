from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.schemas.base import UUIDSchema

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str | None = None
    role: str = "viewer"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase, UUIDSchema):
    is_active: bool
    
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
