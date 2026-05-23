from core.ApiLogic import ApiLogic
from core.Http_Client.schemas.users import UserCreate, UserPatch


class UsersLogic(ApiLogic):
    async def add_user(self, user: UserCreate) -> bool:
        try:
            await self.api.add_user(user)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось добавить пользователя. Повторите попытку.",
                forbidden_message="У вас нет прав на добавление пользователей.",
                conflict_message="Пользователь с таким e-mail уже существует.",
                validation_message="Проверьте e-mail, роль и пароль.",
                unprocessable_message="Проверьте e-mail, роль и пароль.",
            )
            return False

    async def get_users(self):
        try:
            return await self.api.get_users()
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось загрузить список пользователей.",
                forbidden_message="У вас нет прав на просмотр пользователей.",
            )
            return None

    async def delete_user(self, user_id) -> bool:
        try:
            await self.api.delete_user(user_id=user_id)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось удалить пользователя. Повторите попытку.",
                forbidden_message="У вас нет прав на удаление пользователей.",
                not_found_message="Пользователь не найден. Возможно, он уже удалён.",
            )
            return False

    async def patch_user(self, user_id, user: UserPatch) -> bool:
        try:
            await self.api.patch_user(user_id=user_id, user=user)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось изменить пользователя. Повторите попытку.",
                forbidden_message="У вас нет прав на изменение пользователей.",
                not_found_message="Пользователь не найден. Возможно, он уже удалён.",
                conflict_message="Пользователь с таким e-mail уже существует.",
                validation_message="Проверьте e-mail, роль и пароль.",
                unprocessable_message="Проверьте e-mail, роль и пароль.",
            )
            return False
