import asyncio
import json
import random

import websockets
from kivy.app import async_runTouchApp
from kivy.graphics import Color, Line, Rectangle
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

kv = """
WS:
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

client_id = random.randint(1000000, 10000000)


class TestCanvas(Widget):
    """TestCanvas Widget"""

    def on_touch_down(self, touch):
        """Called when a touch down event occurs"""
        if self.collide_point(*touch.pos):
            color = (random.random(), 1, 1)
            with self.canvas:
                Color(*color, mode="hsv")
                touch.ud["line"] = Line(points=(touch.x, touch.y), width=2)

    def on_touch_move(self, touch):
        """Called when a touch move event occurs"""
        if self.collide_point(*touch.pos):
            with self.canvas:
                touch.ud["line"].points += (touch.x, touch.y)

    def on_touch_up(self, touch):
        """Called when a touch up event occurs"""
        if touch.ud.get("line"):
            self.parent.message = json.dumps({"line": touch.ud["line"].points})


class WS(BoxLayout):
    """WS"""

    btn_text = StringProperty("WebSocket Connected")
    layout = ObjectProperty(None)
    message = StringProperty("")
    received = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            if "bg_color" in kwargs:
                bg_rgba = kwargs["bg_color"]
                if len(bg_rgba) == 4:
                    Color(bg_rgba[0], bg_rgba[1], bg_rgba[2], bg_rgba[3])
                elif len(bg_rgba) == 3:
                    Color(bg_rgba[0], bg_rgba[1], bg_rgba[2])
                else:
                    Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

            def update_rect(instance, value):
                instance.bg_rect.pos = instance.pos
                instance.bg_rect.size = instance.size

            # listen to size and position changes
            self.bind(pos=update_rect, size=update_rect)

    def on_received(self, instance, value):
        """Called when received message"""
        self.btn_text = value
        self.update_line(value)

    def update_line(self, message: str):
        """Update lines from other clients"""
        parsed = json.loads(message)
        if parsed["client_id"] != client_id:
            with self.canvas:
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
