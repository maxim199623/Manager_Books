import logging

import httpx
from pydantic import ValidationError

from core.Http_Client.client import ApiClient
from core.Http_Client.errors import ApiError, ConflictError, ForbiddenError, NotFoundError, ServerError
from core.Http_Client.errors import SessionReplacedError, UnauthorizedError, UnprocessableContentError
from core.MessageLevel import MessageLevel
from core.state import AppState

logger = logging.getLogger("app")


class ApiLogic:
    def __init__(self, state: AppState, api: ApiClient):
        self.state = state
        self.api = api

    def _notify(self, message: str, level: MessageLevel = MessageLevel.ERROR) -> None:
        self.state.notify(message=message, level=level)

    def _clear_session(self) -> None:
        if getattr(self.state, "user", None) is not None:
            self.state.clear_user()

    def _handle_api_error(
        self,
        exc: Exception,
        *,
        default_message: str,
        unauthorized_message: str = "Сессия истекла. Войдите снова.",
        forbidden_message: str = "У вас нет прав для этого действия.",
        not_found_message: str = "Объект не найден.",
        conflict_message: str = "Операцию нельзя выполнить из-за конфликта данных.",
        validation_message: str = "Проверьте заполненные поля.",
        unprocessable_message: str = "Проверьте заполненные поля.",
        server_message: str = "Сервер временно недоступен. Повторите попытку позже.",
        network_message: str = "Не удалось связаться с сервером. Проверьте подключение и повторите попытку.",
    ) -> None:
        if isinstance(exc, SessionReplacedError):
            self._notify("Сессия завершена. Войдите снова.", MessageLevel.WARNING)
            self._clear_session()
            return

        if isinstance(exc, UnauthorizedError):
            self._notify(unauthorized_message, MessageLevel.WARNING)
            self._clear_session()
            return

        if isinstance(exc, ForbiddenError):
            self._notify(forbidden_message)
            return

        if isinstance(exc, NotFoundError):
            self._notify(not_found_message)
            return

        if isinstance(exc, ConflictError):
            self._notify(conflict_message)
            return

        if isinstance(exc, ValidationError):
            self._notify(validation_message)
            return

        if isinstance(exc, UnprocessableContentError):
            self._notify(unprocessable_message)
            return

        if isinstance(exc, ServerError):
            self._notify(server_message)
            return

        if isinstance(exc, httpx.TimeoutException):
            self._notify(network_message)
            return

        if isinstance(exc, httpx.RequestError):
            self._notify(network_message)
            return

        if isinstance(exc, ApiError):
            self._notify(default_message)
            return

        logger.exception("Необработанная ошибка в слое API-логики", exc_info=exc)
        self._notify(default_message)
