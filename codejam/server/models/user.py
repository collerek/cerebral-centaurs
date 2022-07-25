from typing import TYPE_CHECKING, List

from starlette.websockets import WebSocket

from codejam.server.interfaces.message import Message

if TYPE_CHECKING:  # pragma: no cover
    from codejam.server.models.game import Game


class User:
    """Represents a player."""

    def __init__(self, username: str, websocket: WebSocket):
        self.username = username
        self.score: int = 0
        self.websocket = websocket
        self.owned_games: List["Game"] = []

    async def send_message(self, message: Message):
        """Broadcast the message to user."""
        print(f"Sending message {message.json()} to user {self.username}")
        await self.websocket.send_json(message.dict())
