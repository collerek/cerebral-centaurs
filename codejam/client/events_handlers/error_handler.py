from typing import Callable, Dict

from codejam.client.events_handlers.base_handler import BaseEventHandler
from codejam.client.events_handlers.utils import display_popup
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ErrorOperations, TopicEnum


class ErrorEventHandler(BaseEventHandler):
    """Handler for error messages."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_callbacks: Dict[str, Callable[[Message], None]] = {
            ErrorOperations.BROADCAST.value: self.display_error
        }

        self.callbacks[TopicEnum.ERROR.value] = self.error_callbacks

    def display_error(self, message: Message) -> None:
        """Display error modal."""
        self.manager.current = "menu_screen"
        self.ids.counter.cancel_animation()
        self.ids.counter.text = "WAITING FOR START"
        display_popup(
            header="Error encountered!",
            title=message.value.exception,
            message=message.value.value,
            additional_message=message.value.error_id,
        )
