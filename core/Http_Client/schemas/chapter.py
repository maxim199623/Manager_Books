import json
import uuid

from pydantic import BaseModel , field_validator, field_serializer
from typing import Optional, List
from datetime import datetime
from base64 import b64encode, b64decode


class ChapterCreate(BaseModel):
    chapter: int
    chapter_name: str
    description: str
    file: Optional[bytes] = None

    # ---------- выход: bytes → base64 ----------
    @field_serializer("file")
    def encode_base64(self, v: bytes | None):
        if v is None:
            return None
        return b64encode(v).decode("ascii")



class ChapterRead(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    chapter: int
    chapter_name: str
    description: str
    file: Optional[bytes] = None
    created_at: datetime

    # ---------- вход: base64 → bytes ----------
    @field_validator( "file", mode="before")
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


class ChapterPatch(BaseModel):
    chapter_name:  Optional[str] = None
    description:  Optional[str] = None
    file: Optional[bytes] = None

    # ---------- выход: bytes → base64 ----------
    @field_serializer("file")
    def encode_base64(self, v: bytes | None):
        if v is None:
            return None
        return b64encode(v).decode("ascii")


class ChapterCount(BaseModel):
    book_id: uuid.UUID
    chapters_count: int


class ChapterReadCount(BaseModel):
    book_id: uuid.UUID
    read_chapters: int

class BookChapterListRead(BaseModel):
    chapter: int
    chapter_name: Optional[str] = None


class ReadChaptersResponse(BaseModel):
    chapters: List[int]


