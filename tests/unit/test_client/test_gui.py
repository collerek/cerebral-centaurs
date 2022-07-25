import json
from typing import Dict

import pytest
from kivy.base import EventLoop
from kivy.graphics import Line
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root


@pytest.fixture(scope="class")
def test_data() -> Dict:
    return {"client_id": 1, "data": {"line": [0, 1, 1, 1], "colour": [0, 0, 0, 1], "width": 2}}


@pytest.fixture(scope="class")
def test_line(request, test_data):
    request.cls.test_line = test_data


@pytest.mark.usefixtures("test_line")
class BasicDrawingTestCase(GraphicUnitTest):
    def test_drawing_line(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = 'whiteboard'
        wb_screen = self.root.current_screen
        self.advance_frames(2)
        canvas = wb_screen.ids.canvas
        assert wb_screen.ids.label.text == "WebSocket Connected"
        canvas.pos = (0, 0)
        touch = UnitTestTouch(x=200, y=200)
        touch.touch_down()
        touch.touch_move(x=100, y=100)
        touch.touch_up()
        colour = canvas.colour
        expected_line = [200.0, 200.0, 100.0, 100.0]
        assert json.loads(wb_screen.wb.message) == {
            "line": expected_line,
            "colour": colour,
            "width": 2,
        }
        self.advance_frames(2)
        assert "line" in touch.ud
        assert isinstance(touch.ud["line"], Line)
        assert touch.ud["line"].points == expected_line

    def test_drawing_line_from_websocket(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root
        self.render(self.root)
        wb_screen = self.root.get_screen('whiteboard')

        wb_screen.wb.received = json.dumps(self.test_line)
        assert json.loads(wb_screen.wb.btn_text) == self.test_line

        for child in self.root.canvas.children:
            if isinstance(child, Line):
                assert child.points == self.test_line["data"]["line"]

        self.render(self.root)
        self.assertLess(len(self._win.children), 2)
