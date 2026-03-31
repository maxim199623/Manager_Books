
import httpx
from core.Http_Client.errors import (
    ApiError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError, UnprocessableContentError, MethodNotAllowedError, ConflictError,
)



def map_http_error(response: httpx.Response):
    match response.status_code:
        case 401:
            raise UnauthorizedError("Не авторизован")
        case 403:
            raise ForbiddenError("Нет доступа")
        case 404:
            raise NotFoundError("Не найдена")
        case 405:
            raise MethodNotAllowedError("Неизвестный метод")
        case 409:
            raise ConflictError("Конфликт")
        case 422:
            raise UnprocessableContentError("Неверные данные")
        case s if 500 <= s < 600:
            raise ServerError("Ошибка сервера")
        case _:
            raise ApiError(response.text)

