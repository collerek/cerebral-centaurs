import uuid
from random import choice, randint
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

    def cancel_previous_tricks(self):
        """To be sure we not apply two tricks at once."""
        Animation.cancel_all(self.cvs)
        self.snail_active = False

    def snail(self, message: Message) -> None:
        """Snail trick handler"""
        self.display_message(message=message)
        self.cancel_previous_tricks()
        self.snail_active = True

    def earthquake(self, message: Message) -> None:
        """Earthquake trick handler"""
        self.display_message(message=message)
        self.cancel_previous_tricks()
        offset = 10
        step_duration = 0.05
        self.current_trick = (
            Animation(offset_x=-offset / 2, duration=step_duration)
            + Animation(offset_x=+offset, duration=step_duration)
            + Animation(offset_x=-offset, duration=step_duration)
            + Animation(offset_x=+offset / 2, duration=step_duration)
        )
        self.current_trick += (
            Animation(offset_y=-offset / 2, duration=step_duration)
            + Animation(offset_y=+offset, duration=step_duration)
            + Animation(offset_y=-offset, duration=step_duration)
            + Animation(offset_y=+offset / 2, duration=step_duration)
        )
        self.current_trick.repeat = True
        self.current_trick.start(self.cvs)

    def landslide(self, message: Message) -> None:
        """Landslide trick handler"""
        self.display_message(message=message)
        self.cancel_previous_tricks()
        offset = choice([150, -150])
        angles = {150: -30, -150: 30}
        angle = angles[offset]
        step_duration = 0.5
        self.current_trick = Animation(
            offset_x=offset, offset_y=-200, angle=angle, duration=step_duration
        )
        self.current_trick.start(self.cvs)

    def packman(self, message: Message) -> None:
        """Handle packman trick"""
        self.cancel_previous_tricks()
        self.display_message(message=message)
        self.line_width = randint(20, 30)
        self.line_x = randint(int(self.cvs.pos[0]), int(self.cvs.pos[0]) + self.cvs.size[0])
        self.line_y = self.cvs.pos[1] + self.cvs.width
        self.anim = Animation(a=0, duration=self.cvs.size[1])
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
        self.cancel_previous_tricks()
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
