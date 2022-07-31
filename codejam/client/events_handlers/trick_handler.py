import uuid
from random import choice, randint
from typing import Callable, Dict, List, Union, cast

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

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
        self.last_direction = None
        self.direction = None
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
        if self.current_trick:
            if isinstance(self.current_trick, Animation):
                self.current_trick.cancel(self.cvs)
            else:
                self.current_trick.cancel()
                if self.pacman_animation:
                    self.pacman_animation.cancel(self)
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
        self.line_width = 15
        self.run_packman()
        self.current_trick = Clock.schedule_interval(self.run_packman, timeout=3)

    def run_packman(self, value=None):
        """Main running pacman function"""
        self.a = 0
        self.line_x = randint(self.cvs.pos[0] + 20, self.cvs.pos[0] + self.cvs.width - 20)
        self.line_y = randint(self.cvs.pos[1] + 20, self.cvs.pos[1] + self.cvs.height - 20)

        self.direction = (
            choice(["vertical", "horizontal"])
            if not self.last_direction
            else ["vertical", "horizontal"][int(self.last_direction == "vertical")]
        )
        self.last_direction = self.direction
        self.pacman_animation = Animation(a=100, duration=0.5)
        self.pacman_animation.start(self)

    def on_a(self, instance: Widget, value: int):
        """Animate on change"""
        self.draw_pacman(value)

    # TODO: Write a test for both paths
    def prepare_pacman_line(self, value: int) -> List[Union[float, int]]:  # pragma: no cover
        """Calculate pacman line coordinates"""
        if self.direction == "horizontal":
            x1 = self.cvs.pos[0] + 20
            y1 = self.line_y
            x2 = self.cvs.pos[0] + ((self.cvs.width - 40) * (value / 100)) + 20
            y2 = self.line_y
        else:
            x1 = self.line_x
            y1 = self.cvs.pos[1] + 20
            x2 = self.line_x
            y2 = self.cvs.pos[1] + ((self.cvs.height - 40) * (value / 100)) + 20
        return [x1, y1, x2, y2]

    def draw_pacman(self, value: int):
        """Send message to others with pacman draw"""
        self.manager.current_screen.second_message = Message(
            topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
            username=self.manager.username,
            game_id=self.manager.game_id,
            value=PictureMessage(
                draw_id=str(uuid.uuid4()),
                data=LineData(
                    colour=[0.2, 0.9, 0.5],
                    line=self.prepare_pacman_line(value),
                    width=self.line_width,
                ),
            ),
        ).json(models_as_dict=True)

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
