import json
from typing import Dict, cast

from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from codejam.server.interfaces.message import Message


class BaseEventHandler(Screen):
    """Base event handler to serve dispatching to handlers."""

    received = StringProperty("")
    received_raw = StringProperty("")
    current_trick = ObjectProperty()
    pacman_animation = ObjectProperty()
    canvas_initial_offset_x = NumericProperty()
    canvas_initial_offset_y = NumericProperty()
    snail_active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callbacks: Dict[str, Dict] = {}

    def on_received(self, instance: Widget, value: str) -> None:
        """Called when received message"""
        self.received_raw = value
        parsed = Message(**json.loads(value))
        callback = self.callbacks[cast(str, parsed.topic.type)][parsed.topic.operation]
        callback(parsed)
