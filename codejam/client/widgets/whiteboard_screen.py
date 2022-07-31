import asyncio
import logging
import pathlib
import string
from random import choices
from typing import List, Union

import websockets
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from websockets.exceptions import ConnectionClosedError

from codejam.client.events_handlers import EventHandler
from codejam.client.events_handlers.utils import display_popup
from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import GameOperations, Topic, TopicEnum

logger = logging.getLogger(__name__)


class WhiteBoardScreen(EventHandler):
    """WhiteBoardScreen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = "ws://127.0.0.1:8000/ws/{0}"

    lobby_widget = ObjectProperty(None)
    layout = ObjectProperty(None)
    message = StringProperty("")
    second_message = StringProperty("")

    def task_callback(self, task: asyncio.Task):
        """Used to handle exceptions inside websocket task."""
        try:
            return task.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be treated as an error.
        except ConnectionRefusedError as e:
            logger.exception(e)
            self.reset_websocket()
            display_popup(
                header="Error encountered!",
                title=e.__class__.__name__,
                message=str(e),
                additional_message="Check your server and internet connections.",
                auto_dismiss=False,
            )
        except ConnectionClosedError as e:
            logger.exception(e)
            self.reset_websocket()
            display_popup(
                header="Connection lost",
                title="You've been disconnected from the server",
                message="Error: " + str(e),
                additional_message="Check your server and internet connections.",
                auto_dismiss=False,
            )
        except Exception as e:
            logger.exception(e)
            self.reset_websocket()
            display_popup(
                header="Unexpected error encountered!",
                title="Unexpected error",
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
        self.canvas_initial_offset_x = self.cvs.offset_x
        self.canvas_initial_offset_y = self.cvs.offset_y
        if not self.manager.ws:
            websocket_task = asyncio.create_task(self.run_websocket())
            websocket_task.add_done_callback(self.task_callback)
            self.manager.ws = websocket_task
        if self.manager.create_room:
            lobby = self.manager.ids.lobby
            lobby.pos_hint = {"center_x": 0.5, "center_y": 0.5}
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

    def on_enter(self) -> None:
        """Called when the screen is shown."""
        Window.bind(mouse_pos=self.mouse_pos)

    def on_pre_leave(self) -> None:
        """Called when the screen is about to be hidden."""
        Window.unbind(mouse_pos=self.mouse_pos)
        self.manager.game_id = "".join(choices(string.ascii_letters + string.digits, k=8))
        self.cancel_trick()
        self.ids.score_board.rebuild_score([])
        self.ids.chat_window.ids.chat_box.clear_widgets()
        self.cvs.canvas.clear()

    anim = None
    top_enter = BooleanProperty(False)
    left_enter = BooleanProperty(False)
    right_enter = BooleanProperty(False)

    def mouse_pos(self, window: Window, pos: List[Union[int, float]]) -> None:
        """Handle mouse position."""
        if pos[0] < Window.width * 0.2 and Window.height * 0.2 < pos[1] < Window.height * 0.8:
            self.left_enter = True
        elif pos[0] > Window.width * 0.7 and Window.height * 0.2 < pos[1] < Window.height * 0.8:
            self.right_enter = True
        else:
            self.top_enter = False
            self.left_enter = False
            self.right_enter = False

    def on_left_enter(self, instance: Widget, value: bool):
        """Handle left enter."""
        if value:
            self.anim = Animation(left_x=0.2, d=0.5)
            self.anim.start(self)
        else:
            if self.anim:
                self.anim.stop(self)
            self.anim = Animation(left_x=0, d=0.5)
            self.anim.start(self)

    def on_right_enter(self, instance: Widget, value: bool):
        """Handle right enter."""
        if value:
            self.anim = Animation(right_x=0.75, d=0.5)
            self.anim.start(self)
        else:
            if self.anim:
                self.anim.stop(self)
            self.anim = Animation(right_x=0.95, d=0.5)
            self.anim.start(self)

    def start_game(self) -> None:
        """Start game"""
        self.message = self._prepare_message(operation=GameOperations.START).json(
            models_as_dict=True
        )
        self.remove_lobby()

    def remove_lobby(self):
        """Remove lobby out of view."""
        lobby = self.manager.ids.lobby
        lobby.pos_hint = {"center_x": 2, "center_y": 2}

    async def run_websocket(self) -> None:
        """Runs the websocket client and send messages."""
        url = self.url.format(self.manager.username)
        logger.debug(url)
        async with websockets.connect(url) as websocket:
            while True:
                if m := self.message:
                    self.message = ""
                    logger.debug("sending " + m)
                    await websocket.send(m)
                if m := self.second_message:
                    self.second_message = ""
                    logger.debug("sending " + m)
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


class InfoPopup(ModalView):
    """ErrorPopup"""

    header = StringProperty("")
    title = StringProperty("")
    message = StringProperty("")
    additional_message = StringProperty("")


root_path = pathlib.Path(__file__).parent.resolve()
Builder.load_file(f'{root_path.joinpath("whiteboard_screen.kv")}')
