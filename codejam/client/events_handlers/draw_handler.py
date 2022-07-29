from typing import Callable, Dict

from kivy.graphics import Color, Line, Rectangle

from codejam.client.events_handlers.base_handler import BaseEventHandler
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import DrawOperations, TopicEnum


class DrawEventHandler(BaseEventHandler):
    """Handler for draw related events."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draw_callbacks: Dict[str, Callable[[Message], None]] = {
            DrawOperations.LINE.value: self.draw_line,
            DrawOperations.RECT.value: self.draw_rectangle,
            DrawOperations.FRAME.value: self.draw_line,
        }

        self.callbacks[TopicEnum.DRAW.value] = self.draw_callbacks

    def draw_line(self, message: Message) -> None:
        """Draw lines from other clients"""
        with self.cvs.canvas:
            Color(hsv=message.value.data.colour)
            line = Line(points=message.value.data.line, width=message.value.data.width)
            self.ids[message.value.draw_id] = line

    def draw_rectangle(self, message: Message) -> None:
        """Draw rectangle from other clients"""
        with self.cvs.canvas:
            Color(hsv=message.value.data.colour)
            rect = Rectangle(pos=message.value.data.pos, size=message.value.data.size)
            self.ids[message.value.draw_id] = rect
