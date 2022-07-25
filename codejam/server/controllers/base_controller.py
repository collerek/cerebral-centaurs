import abc
from typing import Any, Callable, Coroutine, Dict, cast

from codejam.server.connection_manager import ConnectionManager
from codejam.server.interfaces.message import Message


class BaseController(abc.ABC):  # pragma: no cover
    """Base controller that handles messages for different topics"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    @property
    @abc.abstractmethod
    def dispatch_schema(
        self,
    ) -> Dict[str, Callable[[Message], Coroutine[Any, Any, Any]]]:
        """Available routes for different operations."""

    async def dispatch(self, message: Message):
        """Dispatch controller operations."""
        callback = self.dispatch_schema[cast(str, message.topic.operation)]
        return await callback(message)
