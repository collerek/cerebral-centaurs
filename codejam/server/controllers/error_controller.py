from functools import cached_property
from typing import Any, Callable, Coroutine, Dict

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.base_controller import BaseController
from codejam.server.exceptions import GameNotExist
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ErrorOperations


class ErrorController(BaseController):
    """Handles messages for DrawOperations."""

    def __init__(self, manager: ConnectionManager):
        super().__init__(manager=manager)

    @cached_property
    def dispatch_schema(
        self,
    ) -> Dict[str, Callable[[Message], Coroutine[Any, Any, Any]]]:
        """Available routes for different operations."""
        return {
            ErrorOperations.BROADCAST.value: self.broadcast_error,
        }

    async def broadcast_error(self, message: Message):
        """Broadcast error to user or all game users."""
        if not message.game_id:
            user = self.manager.get_user(message.username)
            await user.send_message(message=message)
        else:
            try:
                await self.manager.broadcast(
                    game_id=message.game_id,
                    message=message,
                )
            except GameNotExist:
                message.value.exception = GameNotExist.__name__
                message.value.value = f"Game with id: {message.game_id} does not exist!"
                user = self.manager.get_user(message.username)
                await user.send_message(message=message)
