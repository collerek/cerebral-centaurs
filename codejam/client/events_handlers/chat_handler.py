from typing import Callable, Dict

from codejam.client.events_handlers.base_handler import BaseEventHandler
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ChatOperations, TopicEnum


class ChatEventHandler(BaseEventHandler):
    """Handler for chat related events."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_callbacks: Dict[str, Callable[[Message], None]] = {
            ChatOperations.SAY.value: self.chat_say
        }
        self.callbacks[TopicEnum.CHAT.value] = self.chat_callbacks

    def chat_say(self, message: Message) -> None:
        """Chat message from other clients"""
        if message.username != self.manager.username:
            self.ids.chat_window.add_message(**message.value.dict(), propagate=False)
