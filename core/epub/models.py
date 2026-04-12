from pydantic import BaseModel
from typing import List, Optional

class Chapter(BaseModel):
    title: str
    content: List[str]

class Book(BaseModel):
    cover: Optional[bytes]
    title: List[str]
    author: Optional[str]
    description: Optional[str]
    file_format: str = "epub"
    chapters: List[Chapter]
    series: Optional[str] = None
    file: Optional[bytes]