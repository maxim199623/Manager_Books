from pydantic import BaseModel, EmailStr
from core.users.models import UserRole
from datetime import datetime
from typing import Literal


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class UserCreate(BaseModel):
    email: EmailStr
    role: UserRole
    password: str

class UserPatch(BaseModel):
    email: EmailStr | None = None
    role: UserRole  | None = None
    password: str  | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime


