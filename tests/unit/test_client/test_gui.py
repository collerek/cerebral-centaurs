import json

import pytest
from kivy.base import EventLoop
from kivy.graphics import Line, Rectangle
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage, RectData
from codejam.server.interfaces.topics import (
    DrawOperations,
    ErrorOperations,
    Topic,
    TopicEnum,
)


@pytest.fixture(scope="class")
def test_data() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=PictureMessage(
            data=LineData(line=[0, 1, 1, 1], colour=[0, 0, 0, 1], width=2)
        ),
    )


@pytest.fixture(scope="class")
def test_rectangle() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.RECT),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=PictureMessage(
            data=RectData(pos=(100.0, 100.0), colour=[0, 0, 0, 1], size=(0.0, 0.0))
        ),
    )


@pytest.fixture(scope="class")
def test_error() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.ERROR, operation=ErrorOperations.BROADCAST),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=ErrorMessage(exception="TestExp", value="Test"),
    )


@pytest.fixture(scope="class")
def test_line(request, test_data: Message) -> None:
    request.cls.test_line = test_data


@pytest.fixture(scope="class")
def test_rect(request, test_rectangle: Message) -> None:
    request.cls.test_rectangle = test_rectangle


@pytest.fixture(scope="class")
def test_err(request, test_error: Message) -> None:
    request.cls.test_error = test_error


@pytest.mark.usefixtures("test_line")
@pytest.mark.usefixtures("test_err")
@pytest.mark.usefixtures("test_rect")
class BasicDrawingTestCase(GraphicUnitTest):
    def test_drawing_line(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.pos = (0, 0)
        touch = UnitTestTouch(x=200, y=200)
        touch.touch_down()
        touch.touch_move(x=100, y=100)
        touch.touch_up()
        colour = canvas.colour
        expected_line = [200.0, 200.0, 100.0, 100.0]
        assert json.loads(wb_screen.wb.message) == {
            "topic": self.test_line.topic.dict(),
            "username": self.test_line.username,
            "game_id": self.test_line.game_id,
            "value": {
                "data": {
                    "line": expected_line,
                    "colour": colour,
                    "width": 2,
                }
            },
        }
        self.advance_frames(2)
        assert "line" in touch.ud
        assert isinstance(touch.ud["line"], Line)
        assert touch.ud["line"].points == expected_line

    def test_drawing_rectangle(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.tool = "rect"
        canvas.pos = (0, 0)
        touch = UnitTestTouch(x=200, y=200)
        touch.touch_down()
        touch.touch_move(x=100, y=100)
        touch.touch_up()
        colour = canvas.colour
        assert json.loads(wb_screen.wb.message) == {
            "topic": self.test_rectangle.topic.dict(),
            "username": self.test_rectangle.username,
            "game_id": self.test_rectangle.game_id,
            "value": {
                "data": {
                    "colour": colour,
                    "pos": self.test_rectangle.value.data.pos,
                    "size": self.test_rectangle.value.data.size
                }
            },
        }
        self.advance_frames(2)
        assert "rect" in touch.ud
        assert isinstance(touch.ud["rect"], Rectangle)
        assert list(touch.ud["rect"].pos) == self.test_rectangle.value.data.pos
        assert list(touch.ud["rect"].size) == self.test_rectangle.value.data.size

    def test_drawing_line_from_websocket(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_line = self.test_line.copy(deep=True)
        incoming_line.username = "New user"
        wb_screen.wb.received = incoming_line.json()
        assert json.loads(wb_screen.wb.btn_text) == incoming_line.dict()

        line = next(
            (x for x in wb_screen.wb.canvas.children if isinstance(x, Line)), None
        )
        assert line.points == incoming_line.value.data.line

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_drawing_rectangle_from_websocket(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_rectangle = self.test_rectangle.copy(deep=True)
        incoming_rectangle.username = "New user"
        wb_screen.wb.received = incoming_rectangle.json()
        assert json.loads(wb_screen.wb.btn_text) == incoming_rectangle.dict()

        # TODO: Check if there is a better way to get the object
        rect = next(
            (x for x in wb_screen.wb.canvas.children if isinstance(x, Rectangle)), None
        )
        assert list(rect.pos) == incoming_rectangle.value.data.pos
        assert list(rect.size) == incoming_rectangle.value.data.size

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_displaying_error(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.wb.received = self.test_error.json()
        assert json.loads(wb_screen.wb.btn_text) == self.test_error.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == self.test_error.value.exception
        assert popup.message == self.test_error.value.value

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
