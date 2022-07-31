import uuid
from random import randint
from typing import Callable, Dict, cast

from kivy.animation import Animation
from kivy.properties import NumericProperty

from codejam.client.events_handlers.base_handler import BaseEventHandler
from codejam.client.events_handlers.utils import display_popup
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage
from codejam.server.interfaces.topics import DrawOperations, Topic, TopicEnum, TrickOperations


class TrickEventHandler(BaseEventHandler):
    """Handler for trick related events."""

    a = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = None
        self.line_x = 0
        self.line_y = 0
        self.line_width = 0
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
        canvas = self.manager.current_screen.ids.canvas
        self.line_width = randint(20, 40)
        self.line_x = randint(int(canvas.pos[0]), int(canvas.pos[0]) + canvas.size[0])
        self.line_y = canvas.pos[1] + self.width
        self.anim = Animation(a=0, duration=canvas.size[1])
        self.anim.start(self)

    def on_a(self):
        """Animate on change"""
        self.draw_pacman()

    def draw_pacman(self):
        """Send message to others with pacman draw"""
        self.manager.current_screen.message = Message(
            topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
            username=self.manager.current_screen.manager.username,
            game_id=self.manager.current_screen.manager.game_id,
            value=PictureMessage(
                draw_id=str(uuid.uuid4()),
                data=LineData(
                    colour=[0.1, 0.2, 0.3],
                    line=[self.line_x, self.line_y, self.line_x, self.line_y + 1],
                    width=self.line_width,
                ),
            ),
        ).json(models_as_dict=True)
        self.line_y += 1

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
