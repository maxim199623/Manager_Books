import uuid

from pydantic import BaseModel, field_validator, Field
from enum import Enum
from datetime import datetime, timezone


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    id: uuid.UUID = Field(validation_alias="sub")
    sid: uuid.UUID
    role: UserRole
    exp: datetime

    @field_validator("exp", mode="before")
    def convert_timestamp(cls, v):
        if isinstance(v, int):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        return v

