import asyncio
import json
import pathlib
from typing import Callable, Dict, cast

import websockets
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import Color, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    ChatOperations,
    DrawOperations,
    ErrorOperations,
    GameOperations,
    Topic,
    TopicEnum,
)


class WhiteBoardScreen(Screen):
    """WhiteBoardScreen"""

    lobby_widget = ObjectProperty(None)
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

    def task_callback(self, task: asyncio.Task):
        """Used to handle exceptions inside websocket task."""
        try:
            return task.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be treated as an error.
        except ConnectionRefusedError as e:
            self.reset_websocket()
            self.wb.display_popup(
                header="Error encountered!",
                title=e.__class__.__name__,
                message=str(e),
                additional_message="Check your server and internet connections.",
                auto_dismiss=False,
            )
        except Exception:
            self.reset_websocket()
            self.wb.display_popup(
                header="Unexpected error encountered!",
                title="Unexpected server error",
                message="Please contact administrators.",
                additional_message="",
                auto_dismiss=False,
            )

    def reset_websocket(self):
        """On error display menu again and remove old task."""
        self.manager.ws = None
        self.manager.current = "menu_screen"

    def on_pre_enter(self) -> None:
        """Called when the screen is about to be shown."""
        if not self.manager.ws:
            websocket_task = asyncio.create_task(self.run_websocket())
            websocket_task.add_done_callback(self.task_callback)
            self.manager.ws = websocket_task
        if self.manager.create_room:
            try:
                lobby = self.manager.ids.lobby
                if lobby not in self.children:
                    self.add_widget(lobby)
            # TODO: Write test for this path
            except ReferenceError:  # pragma: no cover
                lobby = Factory.Lobby()
                self.add_widget(lobby)
                self.manager.ids["lobby"] = lobby
            """Create new room"""
            self.message = self._prepare_message(
                operation=GameOperations.CREATE, include_difficulty=True
            ).json(models_as_dict=True)
        else:
            """Join existing room"""
            self.remove_lobby()
            self.message = self._prepare_message(operation=GameOperations.JOIN).json(
                models_as_dict=True
            )

    def start_game(self) -> None:
        """Start game"""
        self.message = self._prepare_message(operation=GameOperations.START).json(
            models_as_dict=True
        )
        self.remove_lobby()

    def remove_lobby(self):
        """Remove lobby if exists."""
        try:
            self.remove_widget(self.manager.ids.lobby)
        # TODO: Write test for this path
        except ReferenceError:  # pragma: no cover
            pass

    def _prepare_message(
        self,
        operation: GameOperations,
        include_game_id: bool = True,
        include_difficulty: bool = False,
    ):
        """Helper to create proper messages."""
        difficulty = self.manager.difficulty if include_difficulty else None
        game_id = self.manager.game_id if include_game_id else None
        return Message(
            topic=Topic(type=TopicEnum.GAME, operation=operation),
            username=self.manager.username,
            game_id=game_id,
            value=GameMessage(success=False, game_id=game_id, difficulty=difficulty),
        )

    def on_received(self, instance: Widget, value: str) -> None:
        """Called when received message"""
        self.btn_text = value
        parsed = Message(**json.loads(value))
        callback = self.callbacks[cast(str, parsed.topic.type)][parsed.topic.operation]
        callback(parsed)

    def chat_say(self, message: Message) -> None:
        """Chat message from other clients"""
        if message.username != self.parent.parent.username:
            self.ids.chat_window.add_message(**message.value.dict(), propagate=False)

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

    def game_join(self, message: Message) -> None:
        """Join game message from other clients"""

    def game_start(self, message: Message) -> None:
        """Start game message from other clients"""
        self.parent.game_active = True

    def play_turn(self, message: Message):
        """Play a game turn."""
        self.cvs.canvas.clear()
        drawer = message.value.turn.drawer
        client = self.parent.parent.username
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
        )

    @staticmethod
    def display_popup(header: str, title: str, message: str, additional_message: str):
        """Displays a popup message!"""
        popup = InfoPopup(
            header=header,
            title=title,
            message=message,
            additional_message=additional_message,
        )
        popup.open()
        Clock.schedule_once(popup.dismiss, 3)

    async def run_websocket(self) -> None:
        """Runs the websocket client and send messages."""
        url = "ws://127.0.0.1:8000/ws/{0}".format(self.manager.username)
        print(url)
        async with websockets.connect(url) as websocket:
            while True:
                if m := self.wb.message:
                    self.wb.message = ""
                    print("sending " + m)
                    await websocket.send(m)
                try:
                    self.wb.received = await asyncio.wait_for(websocket.recv(), timeout=1 / 60)
                except asyncio.exceptions.TimeoutError:
                    continue
                await asyncio.sleep(1 / 60)


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
Builder.load_file(f'{root_path.joinpath("whiteboardscreen.kv")}')
