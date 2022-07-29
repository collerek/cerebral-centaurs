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

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # TODO: refactor
        self.draw_callbacks: Dict[str, Callable[[Message], None]] = {
            DrawOperations.LINE.value: self.draw_line,
            DrawOperations.RECT.value: self.draw_rectangle,
            DrawOperations.FRAME.value: self.draw_line,
        }
        self.game_callbacks: Dict[str, Callable[[Message], None]] = {
            GameOperations.CREATE.value: self.game_create,
            GameOperations.JOIN.value: self.game_join,
            GameOperations.START.value: self.game_start,
            GameOperations.TURN.value: self.play_turn,
            GameOperations.WIN.value: self.update_score,
            GameOperations.MEMBERS.value: self.scoreboard_build,
        }
        self.chat_callbacks: Dict[str, Callable[[Message], None]] = {
            ChatOperations.SAY.value: self.chat_say
        }
        self.error_callbacks: Dict[str, Callable[[Message], None]] = {
            ErrorOperations.BROADCAST.value: self.display_error
        }

        self.callbacks: Dict[str, Dict] = {
            TopicEnum.DRAW.value: self.draw_callbacks,
            TopicEnum.GAME.value: self.game_callbacks,
            TopicEnum.CHAT.value: self.chat_callbacks,
            TopicEnum.ERROR.value: self.error_callbacks,
        }

    def on_received(self, instance: Widget, value: str) -> None:
        """Called when received message"""
        self.btn_text = value
        parsed = Message(**json.loads(value))
        callback = self.callbacks[cast(str, parsed.topic.type)][parsed.topic.operation]
        callback(parsed)

    def chat_say(self, message: Message) -> None:
        """Chat message from other clients"""
        if message.username != self.parent.parent.username:
            self.parent.ids.chat_window.add_message(**message.value.dict(), propagate=False)

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

    def game_create(self, message: Message) -> None:
        """Create game message from other clients"""
        self.parent.game_id = message.value.game_id
        self.manager.ids.score_board.add_joining_player(player=message.username)

    def game_join(self, message: Message) -> None:
        """Join game message from other clients"""
        self.manager.ids.score_board.add_joining_player(player=message.username)

    def scoreboard_build(self, message: Message):
        """Build scoreboard for new client"""
        for member in message.value.members:
            self.manager.ids.score_board.add_joining_player(player=member)

    def game_start(self, message: Message) -> None:
        """Start game message from other clients"""
        self.parent.game_active = True

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
        self.manager.ids.score_board.update_score(message=message)
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


root_path = pathlib.Path(__file__).parent.resolve()
Builder.load_file(f'{root_path.joinpath("whiteboard.kv")}')
