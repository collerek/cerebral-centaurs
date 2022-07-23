import json
from threading import Thread

import websocket
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Line
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
            with self.canvas:
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
    url = "ws://127.0.0.1:8000/ws"
    btn_text = StringProperty("Connect to WebSocket")
    layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WebSocketTest, self).__init__(**kwargs)
        socket_server = self.url
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
        return WS()

    def on_ws_message(self, ws, message):
        """Called when a message is received"""
        self.btn_text = message
        self.logger.info("WebSocket: {}".format(message))

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
