from starlette.websockets import WebSocket

from codejam.server.interfaces.message import Message


class User:
    """Represents a player."""

    def __init__(self, username: str, websocket: WebSocket):
        self.username = username
        self.score: int = 0
        self.websocket = websocket

    async def send_message(self, message: Message):
        """Broadcast the message to user."""
        await self.websocket.send_json(message.dict())
