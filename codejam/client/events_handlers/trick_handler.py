from typing import Callable, Dict, cast

from codejam.client.events_handlers.base_handler import BaseEventHandler
from codejam.client.events_handlers.utils import display_popup
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import TopicEnum, TrickOperations


class TrickEventHandler(BaseEventHandler):
    """Handler for trick related events."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trick_callbacks: Dict[str, Callable[[Message], None]] = {
            TrickOperations.SNAIL.value: self.snail,
            TrickOperations.EARTHQUAKE.value: self.earthquake,
            TrickOperations.LANDSLIDE.value: self.landslide,
            TrickOperations.NOTHING.value: self.nothing,
            TrickOperations.PACMAN.value: self.packman,
        }
        self.callbacks[TopicEnum.TRICK.value] = self.trick_callbacks

    def snail(self, message: Message) -> None:
        """Snail trick handler"""
        self.display_message(message=message)

    def earthquake(self, message: Message) -> None:
        """Earthquake trick handler"""
        self.display_message(message=message)

    def landslide(self, message: Message) -> None:
        """Landslide trick handler"""
        self.display_message(message=message)

    def packman(self, message: Message) -> None:
        """Handle packman trick"""
        self.display_message(message=message)

    def nothing(self, message: Message) -> None:
        """Handle nothing trick - just popup"""
        self.display_message(message=message)

    @staticmethod
    def display_message(message: Message):
        """Display Trick popup."""
        phrase = (
            "BE STRONG!"
            if message.topic.operation != TrickOperations.NOTHING.value
            else "STAY AT PEACE!"
        )
        display_popup(
            header="Dirty Goblin attack!",
            title=cast(str, message.topic.operation),
            message=message.value.description,
            additional_message=phrase,
        )
