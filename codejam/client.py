import json
import random
from threading import Thread

import websocket
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.graphics import Color, Line, Rectangle
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

kv = """
<WS>:
    orientation: 'vertical'
    Button:
        size_hint_y: .25
        font_size: dp(8)
        text_size: self.width, None
        texture_size: self.size
        halign: 'center'
        text: app.btn_text
        on_release: root.run()
    TestCanvas:
"""

Builder.load_string(kv)


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
            App.get_running_app().ws.send(json.dumps({"line": touch.ud["line"].points}))


class KivyWebSocket(websocket.WebSocketApp):
    """KivyWebSocket"""

    def __init__(self, *args, **kwargs):
        super(KivyWebSocket, self).__init__(*args, **kwargs)
        self.logger = Logger
        self.logger.info("WebSocket: logger initialized")


class WS(BoxLayout):
    """WS"""

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

    pressed = False

    def run(self):
        """Called on button release"""
        if not self.pressed:
            self.pressed = True
            app = App.get_running_app()
            app.btn_text = "Connecting to WebSocket"
            Clock.schedule_once(app.ws_connection)


class WebSocketTest(App):
    """Base App Class"""

    ws = None
    url = "ws://127.0.0.1:8000/ws/{0}"
    btn_text = StringProperty("Connect to WebSocket")
    layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.client_id = random.randint(1000000, 10000000)
        super(WebSocketTest, self).__init__(**kwargs)
        socket_server = self.url.format(self.client_id)
        ws = KivyWebSocket(
            socket_server,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_open=self.on_ws_open,
            on_close=self.on_ws_close,
        )
        self.ws = ws
        self.logger = Logger
        self.logger.info("App: initiallzed")

    def build(self):
        """Returns the root widget"""
        self.root = WS()
        self.root.run()
        return self.root

    def on_ws_message(self, ws, message):
        """Called when a message is received"""
        print(json.loads(message))
        self.btn_text = message
        self.logger.info("WebSocket: {}".format(message))
        self.update_line(message)

    @mainthread
    def update_line(self, message: str):
        """Update lines from other clients"""
        app = App.get_running_app()
        parsed = json.loads(message)
        if parsed["client_id"] != self.client_id:
            with app.root.canvas:
                Line(points=parsed["data"]["line"], width=2)

    def on_ws_error(self, ws, error):
        """Called when the websocket has an error"""
        self.logger.info("WebSocket: [ERROR]  {}".format(error))

    def ws_connection(self, dt, **kwargs):
        """Called to start the websocket connection"""
        self.ws_thread = Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def on_ws_open(self, ws):
        """Called when the websocket is opened"""
        self.btn_text = "Connection Open"

    def on_ws_close(self, ws, *args):
        """Called when the websocket is stopped"""
        self.btn_text = "Connection Closed"

    def on_stop(self):
        """Called when the app is stopped"""
        self.ws.keep_running = False


if __name__ == "__main__":
    WebSocketTest().run()
