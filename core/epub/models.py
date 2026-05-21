from pydantic import BaseModel
from typing import List, Optional

class Chapter(BaseModel):
    title: str
    content: str

class Book(BaseModel):
    cover: Optional[bytes]
    title: List[str]
    author: Optional[str]
    description: Optional[str]
    format: str = "epub"
    chapters: List[Chapter]
    series: Optional[str] = None
    file: Optional[bytes]
