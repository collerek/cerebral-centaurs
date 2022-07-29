import asyncio
import pathlib

import websockets
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView

from codejam.client.events_handlers import EventHandler
from codejam.client.events_handlers.utils import display_popup
from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations, Topic, TopicEnum


class WhiteBoardScreen(EventHandler):
    """WhiteBoardScreen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = "ws://127.0.0.1:8000/ws/{0}"

    lobby_widget = ObjectProperty(None)
    layout = ObjectProperty(None)
    message = StringProperty("")

    def task_callback(self, task: asyncio.Task):
        """Used to handle exceptions inside websocket task."""
        try:
            return task.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be treated as an error.
        except ConnectionRefusedError as e:
            self.reset_websocket()
            display_popup(
                header="Error encountered!",
                title=e.__class__.__name__,
                message=str(e),
                additional_message="Check your server and internet connections.",
                auto_dismiss=False,
            )
        except Exception:
            self.reset_websocket()
            display_popup(
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

    async def run_websocket(self) -> None:
        """Runs the websocket client and send messages."""
        url = self.url.format(self.manager.username)
        print(url)
        async with websockets.connect(url) as websocket:
            while True:
                if m := self.message:
                    self.message = ""
                    print("sending " + m)
                    await websocket.send(m)
                try:
                    self.received = await asyncio.wait_for(websocket.recv(), timeout=1 / 60)
                except asyncio.exceptions.TimeoutError:
                    continue
                await asyncio.sleep(1 / 60)  # pragma: no cover

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
Builder.load_file(f'{root_path.joinpath("whiteboard_screen.kv")}')