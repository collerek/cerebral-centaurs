from functools import cached_property
from typing import Any, Callable, Coroutine, Dict

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.base_controller import BaseController
from codejam.server.exceptions import GameNotStarted
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import DrawOperations


class DrawController(BaseController):
    """Handles messages for DrawOperations."""

    def __init__(self, manager: ConnectionManager):
        super().__init__(manager=manager)

    @cached_property
    def dispatch_schema(
        self,
    ) -> Dict[str, Callable[[Message], Coroutine[Any, Any, Any]]]:
        """Available routes for different operations."""
        return {
            DrawOperations.LINE.value: self.broadcast_drawable,
            DrawOperations.RECT.value: self.broadcast_drawable,
            DrawOperations.FRAME.value: self.broadcast_drawable,
        }

    async def broadcast_drawable(self, message: Message):
        """Handles broadcasting the drawables."""
        if not message.game_id:
            raise GameNotStarted("You have to join or create a game before you can draw")
        await self.manager.broadcast(
            game_id=message.game_id,
            message=message,
        )
