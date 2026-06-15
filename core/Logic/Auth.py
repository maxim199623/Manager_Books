import logging

import jwt
from httpx import ConnectError

from core.Http_Client.client import ApiClient
from core.Http_Client.errors import UnauthorizedError, UnprocessableContentError
from core.MessageLevel import MessageLevel
from core.state import AppState
from core.users.models import User

logger = logging.getLogger("app.auth")

class AuthLogic:
    """
    Сценарии авторизации.
    """
    def __init__(self, state: AppState, api: ApiClient, ws):
        self.state = state
        self.api = api
        self.ws = ws

    async def login(self, email: str, password: str) -> None:
        try:
            
            data = await self.api.login(email, password)
            payload = jwt.decode(data.access_token, options={"verify_signature": False})
            user = User.model_validate(payload)
            if self.ws:
                await self.ws.connect(data.access_token, self.api.base_url)
            self.state.set_user(user)
            logger.info("Вход выполнен успешно", extra={"user_id": str(user.id)})

        except UnauthorizedError:
            logger.warning("Вход отклонён", extra={"email": email})
            if email != "default@default.ru":
                self.state.notify("Неверный e-mail или пароль.", level=MessageLevel.ERROR)
        except ConnectError:
            logger.warning(
                "Не удалось выполнить вход: сервер недоступен",
                extra={"email": email},
            )
            self.state.notify(
                "Не удалось подключиться к серверу. Проверьте интернет и повторите попытку.",
                level=MessageLevel.ERROR,
            )
        except UnprocessableContentError:
            logger.warning(
                "Не удалось выполнить вход: некорректный ответ авторизации",
                extra={"email": email},
            )
            self.state.notify("Неверный e-mail или пароль.", level=MessageLevel.ERROR)
        except Exception:
            logger.exception("Непредвиденная ошибка при входе", extra={"email": email})
            self.state.notify(
                "Не удалось выполнить вход. Повторите попытку позже",
                level=MessageLevel.ERROR,
            )

    async def logout(self):
        if self.ws:
            await self.ws.close()
        try:
            if self.api.token:
                await self.api.logout()
        except Exception:
            logger.exception("Ошибка при выходе на сервере, локальная сессия будет очищена")
        finally:
            self.api.token = None
            self.state.clear_user()



