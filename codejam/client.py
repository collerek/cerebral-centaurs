import asyncio
import json
from random import randint, random

import websockets
from kivy.app import async_runTouchApp
from kivy.graphics import Color, Line
from kivy.lang.builder import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

kv = """
WS:
    bg_color: 0, 0, 0, 1
    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            pos: self.pos
            size: self.size
    orientation: 'vertical'
    Label:
        color: 1, 0, 1, 1
        size_hint_y: .25
        font_size: dp(10)
        text_size: self.width, None
        texture_size: self.size
        halign: 'center'
        text: root.btn_text
    TestCanvas:
"""

client_id = randint(1000000, 10000000)


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


class WS(BoxLayout):
    """WS"""

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def on_received(self, instance, value):
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


async def run_app_happily(root, web_socket):
    """Run kivy on the asyncio loop"""
    await async_runTouchApp(root, async_lib="asyncio")
    print("App done")
    web_socket.cancel()


async def run_websocket(root):
    """Runs the websocket client and send messages"""
    url = "ws://127.0.0.1:8000/ws/{0}"
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


if __name__ == "__main__":

    def main():
        """Run the methods asynchronously"""
        root = Builder.load_string(kv)
        web_socket = asyncio.ensure_future(run_websocket(root))
        return asyncio.gather(
            run_app_happily(root, web_socket),
            web_socket,
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
