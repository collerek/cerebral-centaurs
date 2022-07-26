import asyncio
import json
import pathlib
import string
from enum import Enum
from random import choices, random
from typing import Callable, Dict, Tuple, cast

import websockets
from kivy.app import App, async_runTouchApp
from kivy.graphics import Color, Line, Rectangle
from kivy.input import MotionEvent
from kivy.lang.builder import Builder
from kivy.properties import BoundedNumericProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage, RectData
from codejam.server.interfaces.topics import DrawOperations, ErrorOperations, Topic, TopicEnum

root_path = pathlib.Path(__file__).parent.resolve()
full_path = root_path.joinpath("whiteboards.kv")
main_full_path = root_path.joinpath("main.kv")


class Tools(Enum):
    """Enum for all GUI tools to draw"""

    LINE = "line"
    RECT = "rect"


class TestCanvas(Widget):
    """TestCanvas Widget"""

    colour = ListProperty([random(), 1, 1])
    line_width = BoundedNumericProperty(2, min=1, max=50, errorvalue=1)
    tool = StringProperty("line")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drawables: Dict[str, Callable[[MotionEvent], None]] = {
            Tools.LINE.value: self._draw_line,
            Tools.RECT.value: self._draw_rectangle,
        }

        self.updates: Dict[
            str, Callable[[MotionEvent], Tuple[DrawOperations, LineData | RectData]]
        ] = {
            Tools.LINE.value: self._update_line,
            Tools.RECT.value: self._update_rectangle,
        }

    def on_touch_down(self, touch: MotionEvent) -> None:
        """Called when a touch down event occurs"""
        if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
            with self.canvas:
                Color(*self.colour, mode="hsv")
                self.drawables.get(self.tool)(touch)

    def select_operator(
        self, touch_data: Dict
    ) -> Callable[[MotionEvent], Tuple[DrawOperations, LineData | RectData]]:
        """Selects operation based on keys in touc.ud dictionary"""
        constraints = [x.value for x in Tools]
        checks = (key if key in touch_data else None for key in constraints)
        target_class = next((target for target in checks if target is not None), None)
        return self.updates.get(target_class)

    def on_touch_move(self, touch: MotionEvent) -> None:
        """Called when a touch move event occurs"""
        if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
            operator = self.select_operator(touch.ud)
            if operator:
                operation, data = operator(touch)
                root_widget.current_screen.wb.message = self._prepare_message(
                    operation=operation, data=data
                ).json(models_as_dict=True)

    def _draw_line(self, touch: MotionEvent) -> None:
        """Draw a line"""
        touch.ud[Tools.LINE.value] = Line(points=(touch.x, touch.y), width=self.line_width)

    def _update_line(self, touch: MotionEvent) -> Tuple[DrawOperations, LineData]:
        """Update a line"""
        with self.canvas:
            touch.ud[Tools.LINE.value].points += (touch.x, touch.y)
        return self._prepare_line_data(touch=touch)

    @staticmethod
    def _draw_rectangle(touch: MotionEvent) -> None:
        """Draw a rectangle"""
        touch.ud[Tools.RECT.value] = Rectangle(pos=(touch.x, touch.y), size=(0, 0))

    def _update_rectangle(self, touch: MotionEvent) -> Tuple[DrawOperations, RectData]:
        """Update rectangle"""
        if not touch.ud.get("origin"):
            touch.ud["origin"] = (touch.x, touch.y)
        pos = touch.ud["origin"]
        touch.ud[Tools.RECT.value].pos = [min(pos[0], touch.x), min(pos[1], touch.y)]
        touch.ud[Tools.RECT.value].size = [abs(touch.x - pos[0]), abs(touch.y - pos[1])]
        return self._prepare_rectangle_data(touch=touch)

    def _prepare_line_data(self, touch: MotionEvent) -> Tuple[DrawOperations, LineData]:
        """Prepare data for line message."""
        operation = DrawOperations.LINE
        data = LineData(
            line=touch.ud[Tools.LINE.value].points[-4:],
            colour=self.colour,
            width=self.line_width,
        )
        return operation, data

    def _prepare_rectangle_data(self, touch: MotionEvent) -> Tuple[DrawOperations, RectData]:
        """Prepare data for rectangle message."""
        operation = DrawOperations.RECT
        data = RectData(
            pos=touch.ud[Tools.RECT.value].pos,
            colour=self.colour,
            size=touch.ud[Tools.RECT.value].size,
        )
        return operation, data

    @staticmethod
    def _prepare_message(operation: DrawOperations, data: LineData | RectData) -> Message:
        """Prepare the draw message."""
        return Message(
            topic=Topic(type=TopicEnum.DRAW, operation=operation),
            username=root_widget.username,
            game_id=root_widget.game_id,
            value=PictureMessage(data=data),
        )


class WhiteBoard(BoxLayout):
    """WhiteBoard"""

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def on_received(self, instance: Widget, value: str) -> None:
        """Called when received message"""
        # TODO: refactor
        draw_callbacks: Dict[str, Callable[[Message], None]] = {
            DrawOperations.LINE.value: self.draw_line,
            DrawOperations.RECT.value: self.draw_rectangle,
        }
        game_callbacks: Dict[str, Callable[[Message], None]] = {}
        chat_callbacks: Dict[str, Callable[[Message], None]] = {}
        error_callbacks: Dict[str, Callable[[Message], None]] = {
            ErrorOperations.BROADCAST.value: self.display_error
        }

        callbacks: Dict[str, Dict] = {
            TopicEnum.DRAW.value: draw_callbacks,
            TopicEnum.GAME.value: game_callbacks,
            TopicEnum.CHAT.value: chat_callbacks,
            TopicEnum.ERROR.value: error_callbacks,
        }

        self.btn_text = value
        parsed = Message(**json.loads(value))
        callback = callbacks[cast(str, parsed.topic.type)][parsed.topic.operation]
        callback(parsed)

    def draw_line(self, message: Message) -> None:
        """Draw lines from other clients"""
        with self.canvas:
            Color(hsv=message.value.data.colour)
            Line(points=message.value.data.line, width=message.value.data.width)

    def draw_rectangle(self, message: Message) -> None:
        """Draw rectangle from other clients"""
        with self.canvas:
            Color(hsv=message.value.data.colour)
            Rectangle(pos=message.value.data.pos, size=message.value.data.size)

    @staticmethod
    def display_error(message: Message) -> None:
        """Display error modal."""
        popup = ErrorPopup(
            title=message.value.exception,
            message=message.value.value,
            error_code=message.value.error_id,
        )
        popup.open()


class WhiteBoardScreen(Screen):
    """WhiteBoardScreen"""

    def on_pre_enter(self) -> None:
        """Called when the screen is about to be shown."""
        if not self.manager.ws:
            self.manager.ws = asyncio.create_task(self.run_websocket())

    async def run_websocket(self) -> None:
        """Runs the websocket client and send messages."""
        url = "ws://127.0.0.1:8000/ws/{0}".format(self.manager.username)
        try:
            print(url)
            async with websockets.connect(url) as websocket:
                try:
                    while True:
                        if m := self.wb.message:
                            self.wb.message = ""
                            print("sending " + m)
                            await websocket.send(m)
                        try:
                            self.wb.received = await asyncio.wait_for(
                                websocket.recv(), timeout=1 / 60
                            )
                        except asyncio.exceptions.TimeoutError:
                            continue
                        await asyncio.sleep(1 / 60)
                except asyncio.CancelledError as e:
                    print("Loop canceled", e)
                finally:
                    print("Loop finished")
        except (ConnectionRefusedError, asyncio.exceptions.TimeoutError) as e:
            print("Connection refused", e)


class ErrorPopup(ModalView):
    """ErrorPopup"""

    title = StringProperty("")
    message = StringProperty("")
    error_code = StringProperty("")


class ScreenManager(App):
    """Root application"""

    username = StringProperty("")
    game_id = StringProperty("")

    def build(self):
        """Setup username and game_id"""
        # TODO: Later set it up on frontend
        built = Builder.load_file(f"{main_full_path}")
        built.username = "".join(choices(string.ascii_letters + string.digits, k=8))
        built.game_id = "randomGame"
        return built


Builder.load_file(f"{full_path}")
root_widget = ScreenManager().build()

if __name__ == "__main__":  # pragma: no cover

    async def run_app(root_widget):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(root_widget, async_lib="asyncio")
        if root_widget.ws:
            root_widget.ws.cancel()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_app(root_widget))
    loop.close()
