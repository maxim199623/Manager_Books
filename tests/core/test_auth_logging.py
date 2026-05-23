import logging
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ConnectError, Request

from core.Auth import AuthLogic
from core.Http_Client.errors import UnauthorizedError, UnprocessableContentError
from core.MessageLevel import MessageLevel


class StateStub:
    def __init__(self) -> None:
        self.notifications = []
        self.user = None

    def notify(self, message, level=MessageLevel.ERROR) -> None:
        self.notifications.append((message, level))

    def set_user(self, user) -> None:
        self.user = user


def _token_payload() -> dict:
    return {
        "sub": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "role": "user",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }


@pytest.mark.asyncio
async def test_login_logs_connect_error(caplog) -> None:
    state = StateStub()
    api = SimpleNamespace(
        login=AsyncMock(
            side_effect=ConnectError(
                "boom",
                request=Request("POST", "https://example.com/users/auth"),
            )
        ),
        base_url="https://example.com",
    )
    auth = AuthLogic(state, api, ws=AsyncMock())

    with caplog.at_level(logging.WARNING, logger="app.auth"):
        await auth.login("user@example.com", "secret")

    assert any(
        record.name == "app.auth"
        and record.getMessage() == "Login failed: server unavailable"
        for record in caplog.records
    )
    assert state.notifications == [
        (
            "Не удалось подключиться к серверу. Проверьте интернет и повторите попытку.",
            MessageLevel.ERROR,
        )
    ]


@pytest.mark.asyncio
async def test_login_logs_unauthorized_error_for_non_default_user(caplog) -> None:
    state = StateStub()
    api = SimpleNamespace(
        login=AsyncMock(side_effect=UnauthorizedError("boom")),
        base_url="https://example.com",
    )
    auth = AuthLogic(state, api, ws=AsyncMock())

    with caplog.at_level(logging.WARNING, logger="app.auth"):
        await auth.login("user@example.com", "secret")

    assert any(
        record.name == "app.auth" and record.getMessage() == "Login rejected"
        for record in caplog.records
    )
    assert state.notifications == [("Неверный e-mail или пароль.", MessageLevel.ERROR)]


@pytest.mark.asyncio
async def test_login_logs_unprocessable_content_error(caplog) -> None:
    state = StateStub()
    api = SimpleNamespace(
        login=AsyncMock(side_effect=UnprocessableContentError("boom")),
        base_url="https://example.com",
    )
    auth = AuthLogic(state, api, ws=AsyncMock())

    with caplog.at_level(logging.WARNING, logger="app.auth"):
        await auth.login("user@example.com", "secret")

    assert any(
        record.name == "app.auth"
        and record.getMessage() == "Login failed: invalid credentials payload"
        for record in caplog.records
    )
    assert state.notifications == [("Неверный e-mail или пароль.", MessageLevel.ERROR)]


@pytest.mark.asyncio
async def test_login_logs_unexpected_error(caplog) -> None:
    state = StateStub()
    api = SimpleNamespace(
        login=AsyncMock(return_value=SimpleNamespace(access_token="token")),
        base_url="https://example.com",
    )
    auth = AuthLogic(state, api, ws=AsyncMock())

    with caplog.at_level(logging.ERROR, logger="app.auth"):
        await auth.login("user@example.com", "secret")

    assert any(
        record.name == "app.auth"
        and record.getMessage() == "Unexpected login failure"
        for record in caplog.records
    )
    assert state.notifications == [
        ("Не удалось выполнить вход. Повторите попытку позже", MessageLevel.ERROR)
    ]
