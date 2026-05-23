import logging
from types import SimpleNamespace

import pytest

from core.Http_Client.websocket_client import WebSocketClient
from core.MessageLevel import MessageLevel


class TaskStub:
    def __init__(self, done_result: bool) -> None:
        self._done_result = done_result

    def done(self) -> bool:
        return self._done_result


class StateStub:
    def __init__(self) -> None:
        self.notifications = []
        self.clear_user_called = False
        self.current_route = "/books"
        self.is_authenticated = True

    def clear_user(self) -> None:
        self.clear_user_called = True

    def notify(self, message, level=MessageLevel.ERROR) -> None:
        self.notifications.append((message, level))

    def changes_route(self, route: str) -> None:
        self.current_route = route


@pytest.mark.asyncio
async def test_connect_logs_duplicate_connect_guard(caplog) -> None:
    state = StateStub()
    page = SimpleNamespace(run_task=lambda coro: coro)
    client = WebSocketClient(page=page, state=state)
    client._task = TaskStub(done_result=False)

    with caplog.at_level(logging.DEBUG, logger="app.ws"):
        await client.connect("token", "https://example.com")

    assert any(
        record.name == "app.ws"
        and record.getMessage() == "Skipping duplicate WebSocket connect"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_handle_relogin_logs_warning(caplog) -> None:
    state = StateStub()
    page = SimpleNamespace(run_task=lambda coro: coro)
    client = WebSocketClient(page=page, state=state)

    with caplog.at_level(logging.WARNING, logger="app.ws"):
        await client._handle_message({"type": "re_login", "message": "Session replaced"})

    assert any(
        record.name == "app.ws"
        and record.getMessage() == "Session replaced event received"
        for record in caplog.records
    )
    assert state.clear_user_called is True
    assert state.notifications == [("Session replaced", MessageLevel.WARNING)]
