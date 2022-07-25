from functools import cached_property
from typing import Any, Callable, Coroutine, Dict

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.base_controller import BaseController
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ChatOperations


class ChatController(BaseController):
    """Handles messages for ChatOperations."""

    def __init__(self, manager: ConnectionManager):
        super().__init__(manager=manager)

    @cached_property
    def dispatch_schema(
        self,
    ) -> Dict[str, Callable[[Message], Coroutine[Any, Any, Any]]]:
        """Available routes for different operations."""
        return {ChatOperations.SAY.value: self.say}

    async def say(self, message: Message):
        """Handles sending the chat message."""
        await self.manager.broadcast(
            game_id=message.game_id,
            message=message,
        )
