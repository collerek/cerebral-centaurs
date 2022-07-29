import json
import pathlib
from typing import Callable, Dict, cast

from kivy.graphics import Color, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import Clock, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    ChatOperations,
    DrawOperations,
    ErrorOperations,
    GameOperations,
    TopicEnum,
)


class WhiteBoard(BoxLayout):
    """WhiteBoard"""

    def play_turn(self, message: Message):
        """Play a game turn."""
        self.cvs.canvas.clear()
        drawer = message.value.turn.drawer
        client = self.parent.parent.username
        duration = message.value.turn.duration
        self.parent.ids.counter.a = duration
        self.parent.ids.counter.start()
        self.parent.parent.can_draw = drawer == client
        drawing_person = "your" if client == drawer else drawer
        phrase = message.value.turn.phrase if client == drawer else ""
        action = "draw" if client == drawer else "guess"
        self.display_popup(
            header="Next turn!",
            title=f"Now is {drawing_person} turn to draw!",
            message=f"You have {message.value.turn.duration} seconds to {action}!",
            additional_message=phrase,
        )

    def update_score(self, message: Message):
        """Display winner."""
        winner = message.value.turn.winner
        client = self.parent.parent.username
        self.parent.ids.counter.cancel_animation()
        self.parent.ids.counter.text = "WAITING FOR START"
        header = "You WON!" if client == winner else f"Player {message.value.turn.winner} WON!"
        self.display_popup(
            header=header,
            title="The phrase guessed was:",
            message=message.value.turn.phrase,
            additional_message="Next turn will start in 5 seconds!",
        )

    def display_error(self, message: Message) -> None:
        """Display error modal."""
        self.parent.parent.current = "menu_screen"
        self.display_popup(
            header="Error encountered!",
            title=message.value.exception,
            message=message.value.value,
            additional_message=message.value.error_id,
            auto_dismiss=False,
        )

    @staticmethod
    def display_popup(
        header: str,
        title: str,
        message: str,
        additional_message: str,
        auto_dismiss: bool = True,
    ) -> None:
        """Displays a popup message!"""
        popup = InfoPopup(
            header=header,
            title=title,
            message=message,
            additional_message=additional_message,
        )
        popup.open()
        if auto_dismiss:
            Clock.schedule_once(popup.dismiss, 3)


class Instructions(BoxLayout):
    """Instructions rule"""

    _canvas = ObjectProperty(None)


class CanvasTools(BoxLayout):
    """CanvasTools rule"""

    ...


class InfoPopup(ModalView):
    """ErrorPopup"""

    header = StringProperty("")
    title = StringProperty("")
    message = StringProperty("")
    additional_message = StringProperty("")
