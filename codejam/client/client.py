import asyncio
import json
import pathlib
import string
from random import choices, random

import websockets
from kivy.app import async_runTouchApp
from kivy.graphics import Color, Line
from kivy.input import MotionEvent
from kivy.lang.builder import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage
from codejam.server.interfaces.topics import DrawOperations, Topic, TopicEnum

client_id = "".join(choices(string.ascii_letters + string.digits, k=8))
game_id = "randomGame"

root_path = pathlib.Path(__file__).parent.resolve()
full_path = root_path.joinpath("whiteboards.kv")


class TestCanvas(Widget):
    """TestCanvas Widget"""

    colour = ListProperty([random(), 1, 1])

    def on_touch_down(self, touch: MotionEvent) -> None:
        """Called when a touch down event occurs"""
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(*self.colour, mode="hsv")
                touch.ud["line"] = Line(points=(touch.x, touch.y), width=2)

    def on_touch_move(self, touch: MotionEvent) -> None:
        """Called when a touch move event occurs"""
        if self.collide_point(*touch.pos):
            if touch.ud.get("line"):
                with self.canvas:
                    touch.ud["line"].points += (touch.x, touch.y)
                self.parent.message = Message(
                    topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
                    username=client_id,
                    game_id=game_id,
                    value=PictureMessage(
                        data=LineData(
                            line=touch.ud["line"].points[-4:], colour=[*self.colour]
                        )
                    ),
                ).json(models_as_dict=True)


class WhiteBoard(BoxLayout):
    """WhiteBoard"""

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def on_received(self, instance, value: str) -> None:
        """Called when received message"""
        self.btn_text = value
        self.update_line(value)

    def update_line(self, message: str) -> None:
        """Update lines from other clients"""
        parsed = Message(**json.loads(message))
        if parsed.username != client_id:
            with self.canvas:
                Color(hsv=parsed.value.data.colour)
                Line(points=parsed.value.data.line, width=2)


root_widget = Builder.load_file(f"{full_path}")


async def run_websocket(widget: WhiteBoard) -> None:
    """Runs the websocket client and send messages"""
    url = "ws://127.0.0.1:8000/ws/{0}/{1}".format(client_id, game_id)
    try:
        print(url)
        async with websockets.connect(url) as websocket:
            try:
                while True:
                    if m := widget.message:
                        widget.message = ""
                        print("sending " + m)
                        await websocket.send(m)
                    try:
                        widget.received = await asyncio.wait_for(
                            websocket.recv(), timeout=1 / 60
                        )
                    except asyncio.exceptions.TimeoutError:
                        continue
                    await asyncio.sleep(1 / 60)
            except asyncio.CancelledError as e:
                print("Loop canceled", e)
            finally:
                print("Loop finished")
    except ConnectionRefusedError as e:
        print("Connection refused", e)


if __name__ == "__main__":  # pragma: no cover

    async def run_app_happily(widget: WhiteBoard, web_socket: asyncio.Future):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(widget, async_lib="asyncio")
        print("App done")
        web_socket.cancel()

    def main():
        """Run the methods asynchronously"""
        web_socket = asyncio.ensure_future(run_websocket(root_widget))
        return asyncio.gather(
            run_app_happily(root_widget, web_socket),
            web_socket,
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
