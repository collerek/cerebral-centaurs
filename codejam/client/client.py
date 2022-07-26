import asyncio
import json
import pathlib
import string
from random import choices, random

import websockets
from kivy.app import async_runTouchApp
from kivy.graphics import Color, Line, Rectangle
from kivy.input import MotionEvent
from kivy.lang.builder import Builder
from kivy.properties import BoundedNumericProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage, RectData
from codejam.server.interfaces.topics import DrawOperations, Topic, TopicEnum

client_id = "".join(choices(string.ascii_letters + string.digits, k=8))
game_id = "randomGame"

root_path = pathlib.Path(__file__).parent.resolve()
full_path = root_path.joinpath("whiteboards.kv")
main_full_path = root_path.joinpath("main.kv")


class TestCanvas(Widget):
    """TestCanvas Widget"""

    colour = ListProperty([random(), 1, 1])
    line_width = BoundedNumericProperty(2, min=1, max=50, errorvalue=1)
    tool = StringProperty("line")

    def on_touch_down(self, touch: MotionEvent) -> None:
        """Called when a touch down event occurs"""
        if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
            with self.canvas:
                Color(*self.colour, mode="hsv")
                if self.tool == "line":
                    touch.ud["line"] = Line(points=(touch.x, touch.y), width=self.line_width)
                elif self.tool == "rect":
                    touch.ud["rect"] = Rectangle(pos=(touch.x, touch.y), size=(0, 0))

    def on_touch_move(self, touch: MotionEvent) -> None:
        """Called when a touch move event occurs"""
        if self.collide_point(touch.x - self.offset_x, touch.y - self.offset_y):
            if touch.ud.get("line"):
                with self.canvas:
                    touch.ud["line"].points += (touch.x, touch.y)
                op = DrawOperations.LINE
                data = LineData(
                    line=touch.ud["line"].points[-4:],
                    colour=self.colour,
                    width=self.line_width,
                )
            elif touch.ud.get("rect"):
                if not touch.ud.get("origin"):
                    touch.ud["origin"] = (touch.x, touch.y)
                pos = touch.ud["origin"]
                touch.ud["rect"].pos = min(pos[0], touch.x), min(pos[1], touch.y)
                touch.ud["rect"].size = abs(touch.x - pos[0]), abs(touch.y - pos[1])
                op = DrawOperations.RECT
                data = RectData(
                    pos=touch.ud["rect"].pos,
                    colour=self.colour,
                    size=touch.ud["rect"].size,
                )
            else:
                return
            root_widget.current_screen.wb.message = Message(
                topic=Topic(type=TopicEnum.DRAW, operation=op),
                username=client_id,
                game_id=game_id,
                value=PictureMessage(data=data),
            ).json(models_as_dict=True)


class WhiteBoard(BoxLayout):
    """WhiteBoard"""

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def on_received(self, instance: Widget, value: str) -> None:
        """Called when received message"""
        self.btn_text = value
        parsed = Message(**json.loads(value))
        if parsed.username == client_id:
            return
        if parsed.topic.type == TopicEnum.DRAW:
            self.update_line(parsed)

    def update_line(self, message: Message) -> None:
        """Update lines from other clients"""
        with self.canvas:
            if message.topic.operation == DrawOperations.LINE:
                Color(hsv=message.value.data.colour)
                Line(points=message.value.data.line, width=message.value.data.width)
            elif message.topic.operation == DrawOperations.RECT:
                Color(hsv=message.value.data.colour)
                Rectangle(pos=message.value.data.pos, size=message.value.data.size)


class WhiteBoardScreen(Screen):
    """WhiteBoardScreen"""

    def on_pre_enter(self) -> None:
        """Called when the screen is about to be shown."""
        if not self.manager.ws:
            self.manager.ws = asyncio.create_task(self.run_websocket())

    async def run_websocket(self) -> None:
        """Runs the websocket client and send messages."""
        url = "ws://127.0.0.1:8000/ws/{0}".format(client_id)
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


Builder.load_file(f"{full_path}")
root_widget = Builder.load_file(f"{main_full_path}")

if __name__ == "__main__":  # pragma: no cover

    async def run_app(root_widget):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(root_widget, async_lib="asyncio")
        if root_widget.ws:
            root_widget.ws.cancel()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_app(root_widget))
    loop.close()
