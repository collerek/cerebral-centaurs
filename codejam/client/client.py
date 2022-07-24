import asyncio
import json
import pathlib
from random import randint, random

import websockets
from kivy.app import App, async_runTouchApp
from kivy.graphics import Color, Line
from kivy.lang.builder import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

client_id = randint(1000000, 10000000)

root_path = pathlib.Path(__file__).parent.resolve()
full_path = root_path.joinpath("whiteboards.kv")


class TestCanvas(Widget):
    """TestCanvas Widget"""

    colour = ListProperty([random(), 1, 1])

    def on_touch_down(self, touch):
        """Called when a touch down event occurs"""
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(*self.colour, mode="hsv")
                touch.ud["line"] = Line(points=(touch.x, touch.y), width=2)

    def on_touch_move(self, touch):
        """Called when a touch move event occurs"""
        if self.collide_point(*touch.pos):
            if touch.ud.get("line"):
                with self.canvas:
                    touch.ud["line"].points += (touch.x, touch.y)
                self.parent.message = json.dumps(
                    {"line": touch.ud["line"].points[-4:], "colour": self.colour}
                )


class WhiteBoard(BoxLayout):
    """WhiteBoard"""

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def on_received(self, instance, value: str):
        """Called when received message"""
        self.btn_text = value
        self.update_line(value)

    def update_line(self, message: str):
        """Update lines from other clients"""
        parsed = json.loads(message)
        if parsed["client_id"] != client_id:
            with self.canvas:
                Color(hsv=parsed["data"]["colour"])
                Line(points=parsed["data"]["line"], width=2)


class MainApp(App):
    """Main application"""

    def build(self):
        """Builder from whiteboards.kv"""
        return Builder.load_file(f"{full_path}")


root = MainApp().build()


async def run_websocket(root):
    """Runs the websocket client and send messages"""
    url = "ws://127.0.0.1:8000/ws/{0}"
    try:
        async with websockets.connect(url.format(client_id)) as websocket:
            try:
                while True:
                    if m := root.message:
                        root.message = ""
                        print("sending " + m)
                        await websocket.send(m)
                    try:
                        root.received = await asyncio.wait_for(
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

    async def run_app_happily(root, web_socket):
        """Run kivy on the asyncio loop"""
        await async_runTouchApp(root, async_lib="asyncio")
        print("App done")
        web_socket.cancel()

    def main():
        """Run the methods asynchronously"""
        web_socket = asyncio.ensure_future(run_websocket(root))
        return asyncio.gather(
            run_app_happily(root, web_socket),
            web_socket,
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
