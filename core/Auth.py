from core.Http_Client.client import ApiClient
from core.Http_Client.errors import ApiError
from core.state import MessageLevel
from core.users.models import User
import jwt

class AuthLogic:
    """
    Сценарии авторизации.
    """

    def __init__(self, state, api: ApiClient):
        self.state = state
        self.api = api

    async def login(self, email: str, password: str) -> None:
        #TODO исправить try
        try:
            data = await self.api.login(email, password)
            payload = jwt.decode(data.access_token, options={"verify_signature": False})
            user = User.model_validate(payload)
            self.state.set_user(user)

        except ApiError as exc:
            self.state.notify(message=str(exc), level=MessageLevel.ERROR)

        except Exception as exc:
            # на случай непредвиденных ошибок
            ic()
            ic(payload, user)
            self.state.notify(message=f"Ошибка авторизации: {exc}", level=MessageLevel.ERROR)

