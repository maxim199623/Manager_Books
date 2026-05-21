import uuid
from datetime import datetime
from pydantic import BaseModel , field_validator, field_serializer, Field, StringConstraints
from typing import Optional, Annotated

from base64 import b64encode , b64decode


class FileData(BaseModel):
    data: bytes
    filename: str
    content_type: str

class BookCreate(BaseModel):
    title: str
    author: Optional[str] = None
    description: str
    series: Optional[str] = None
    format: Optional[str] = None
    cover: Optional[bytes] = None
    file: Optional[bytes] = None

    # ---------- выход: bytes → base64 ----------
    @field_serializer("cover", "file")
    def encode_base64(self, v: bytes | None):
        if v is None:
            return None
        return b64encode(v).decode("ascii")

    @field_validator("title",  mode="before")
    @classmethod
    def str_title(cls, title):
        if isinstance(title, str):
            title = title.strip()
            return title
        if isinstance(title, (list, tuple)):
            return " / ".join(map(str, title))
        return str(title)


class BookRead(BaseModel):
    id: uuid.UUID
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    series: Optional[str] = None
    format: Optional[str] = None
    cover: Optional[bytes] = None
    file: Optional[bytes] = None
    created_at: datetime

    # ---------- вход: base64 → bytes ----------
    @field_validator("cover", "file", mode="before")
    @classmethod
    def decode_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            return v  # уже декодировано
        if isinstance(v, str):
            try:
                return b64decode(v)
            except Exception as e:
                raise ValueError("Invalid base64 data") from e
        raise TypeError("Expected base64 string or bytes")


class BookUpdate(BookCreate):
    title: Optional[str] = None
    description: Optional[str] = None


