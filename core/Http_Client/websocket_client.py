import json
import logging
import ssl
from pathlib import Path

import websockets
from websockets.exceptions import ConnectionClosed

from core.MessageLevel import MessageLevel

logger = logging.getLogger("websocket")

class WebSocketClient:
    def __init__(self, page, state):
        self.ws = None
        self._task = None
        self.page = page
        self.state = state


    async def connect(self, token: str, base_url: str):
        ic()
        if self._task and not self._task.done():
            ic()
            return

        cert_path = "cert.pem"
        ssl_context = ssl.create_default_context(cafile=str(cert_path))
        ws_base = base_url.replace("https://", "wss://")
        url = f"{ws_base}/ws/notifications?token={token}"
        ic(url)
        self.ws = await websockets.connect(url, ssl=ssl_context)
        self._task = self.page.run_task(self._listen)
        logger.info("WebSocket соединение открыто")

    async def _listen(self):
        ic()
        try:
            async for message in self.ws:
                data = json.loads(message)
                ic(data)
                await self._handle_message(data)
        except ConnectionClosed:
            logger.info("WebSocket соединение закрыто")
        except Exception:
            logger.exception("Ошибка в WebSocket listener")

    async def _handle_message(self, data: dict):
        ic(data)
        msg_type = data.get("type")

        if msg_type == "re_login" and self.state:
            self.state.clear_user()
            self.state.notify(
                data.get("message", "Вы вошли с другого устройства"),
                MessageLevel.WARNING,
            )

        elif msg_type == "new_book" and self.state:
            if self.state.current_route == "/books":
                self.state.changes_route("/books")
            if self.state.is_authenticated:
                self.state.notify(
                f"Добавлена новая книга: {data.get('title')}",
                MessageLevel.INFO,
            )

        elif msg_type == "del_book" and self.state:
            if self.state.current_route == "/books":
                self.state.changes_route("/books")

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
        if self._task is not None:
            self._task.cancel()
            self._task = None