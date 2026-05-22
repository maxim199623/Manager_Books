from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Chapter(BaseModel):
    title: str
    content: str

class Book(BaseModel):
    cover: Optional[bytes]
    title: List[str]
    author: Optional[str]
    description: Optional[str]
    genres: Optional[str] = None
    format: str = "epub"
    chapters: List[Chapter]
    series: Optional[str] = None
    file: Optional[bytes]

class BookGenre(str, Enum):
    FANTASY = "Фэнтези"
    SCIENCE_FICTION = "Научная фантастика"
    DETECTIVE = "Детектив"
    THRILLER = "Триллер"
    MYSTERY = "Мистика"
    HORROR = "Ужасы"
    ROMANCE = "Романтика"
    ADVENTURE = "Приключения"
    HISTORICAL = "Исторический роман"
    DRAMA = "Драма"
    BIOGRAPHY = "Биография"
    AUTOBIOGRAPHY = "Автобиография"
    MEMOIR = "Мемуары"
    DYSTOPIA = "Антиутопия"
    UTOPIA = "Утопия"
    PHILOSOPHICAL = "Философская литература"
