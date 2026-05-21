from httpx import ConnectError

from core.Http_Client.websocket_client import WebSocketClient
from core.MessageLevel import MessageLevel
from core.Http_Client.client import ApiClient
from core.Http_Client.errors import ApiError
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


        except ApiError as exc:
            self.state.notify(message=str(exc), level=MessageLevel.ERROR)

        except ConnectError as exc:
            ic(exc)
            self.state.notify(message=f"Ошибка подключения к серверу", level=MessageLevel.ERROR)

        except Exception as exc:
            ic(exc)
            self.state.notify(message=f"Ошибка авторизации: {exc}", level=MessageLevel.ERROR)

    async def logout(self):
        if self.ws:
            await self.ws.close()
        await self.api.logout()
        self.state.clear_user()



