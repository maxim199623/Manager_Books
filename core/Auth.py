from httpx import ConnectError

from core.MessageLevel import MessageLevel
from core.Http_Client.client import ApiClient
from core.Http_Client.errors import ApiError, UnauthorizedError, UnprocessableContentError
from core.state import  AppState
from core.users.models import User
import jwt

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
            if ic(self.ws):
                ic()
                await self.ws.connect(data.access_token, self.api.base_url)
            self.state.set_user(user)


        except UnauthorizedError as exc:
            if email != "default@default.ru":
                self.state.notify(message=str("Неверный e-mail или пароль."), level=MessageLevel.ERROR)

        except ConnectError as exc:
            ic(exc)
            self.state.notify(message=f"Не удалось подключиться к серверу. Проверьте интернет и повторите попытку.", level=MessageLevel.ERROR)

        except UnprocessableContentError as exc:
            ic(exc)
            self.state.notify(message=f"Неверный e-mail или пароль.", level=MessageLevel.ERROR)

        except Exception as exc:
            ic(exc)
            self.state.notify(message=f"Не удалось выполнить вход. Повторите попытку позже", level=MessageLevel.ERROR)

    async def logout(self):
        if self.ws:
            await self.ws.close()
        await self.api.logout()
        self.state.clear_user()



