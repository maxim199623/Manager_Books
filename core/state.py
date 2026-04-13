import logging
import time
from enum import Enum
from typing import Optional, List, Callable, Literal, Dict

from Http_Client.schemas.books import BookRead
from core.config import APISetting, Settings
from core.users.models import User, UserRole

Topic = Literal["user", "book", "message", "route"]
logger = logging.getLogger("app")

class MessageLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AppState:
    """
    Глобальное состояние приложения.
    """
    def __init__(self):
        self.message: str | None = None
        self.message_level: MessageLevel = MessageLevel.ERROR

        self.user: Optional[User] = None
        self.current_book_id: Optional[int] = None
        self.current_book: Optional[BookRead] = None

        self.settings_API: APISetting = Settings().api_config()

        self.current_route: str = "/login"

        self._subscribers: Dict[Topic, List[Callable[[], None]]] = {
            "user": [],
            "book": [],
            "message": [],
            "route": []
        }

    @property
    def is_authenticated(self) -> bool:
        """Проверка авторизации"""
        ic()
        ic(self.user)
        return ic(self.user is not None)

    @property
    def role(self) -> Optional[UserRole]:
        """Проверка роли"""
        ic()
        return ic(self.user.role if self.user else None)


    def subscribe(self, topic: Topic, callback: Callable[[], None]):
        self._subscribers[topic].append(callback)

    def _notify(self, topic: Topic):
        for callback in self._subscribers[topic]:
            callback()

    def set_user(self, user: User):
        self.user = user
        logger.info(f"Выполнен вход пользователя с id:{self.user.id}")
        self._notify("user")

    def clear_user(self):
        logger.info(f"Выход пользователя с id:{self.user.id}")
        self.user = None
        self.current_book_id = None
        self._notify("user")

    def select_book(self, book_id: int, book:BookRead):
        self.current_book_id = book_id
        self.current_book = book
        logger.info(f"Открыта книга с id:{self.current_book_id}")
        self._notify("book")

    def clear_selected_book(self) -> None:
        logger.info(f"Закрыта книга с id:{self.current_book_id}")
        self.current_book_id = None
        self._notify("book")

    def changes_route(self, route) -> None:
        self.current_route = route
        logger.debug(f"Переход на страницу: {self.current_route}")
        self._notify("route")

    def notify(self, message: str, level: MessageLevel = MessageLevel.ERROR) -> None:
        ic()
        self.message = message
        self.message_level = level
        logger.debug(f"Отправлено уведомление: {self.message} с уровнем {self.message_level}")
        self._notify("message")


    def clear_message(self) -> None:
        ic()
        logger.debug(f"Очищено уведомление: {self.message}")
        self.message = None
