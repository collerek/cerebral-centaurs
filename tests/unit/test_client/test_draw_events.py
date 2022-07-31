import json

import pytest
from kivy.base import EventLoop
from kivy.factory import Factory
from kivy.graphics import Line, Rectangle
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget
from codejam.client.widgets.chat_window import Chat
from codejam.client.widgets.draw_canvas import Tools
from codejam.server.interfaces.chat_message import ChatMessage
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.game_message import GameMessage, TurnMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage, RectData
from codejam.server.interfaces.topics import (
    ChatOperations,
    DrawOperations,
    ErrorOperations,
    GameOperations,
    Topic,
    TopicEnum,
    TrickOperations,
)
from codejam.server.interfaces.trick_message import TrickMessage
from codejam.server.models.phrase_generator import PhraseDifficulty


@pytest.fixture(scope="class")
def test_line() -> Message:
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
            data=RectData(pos=[100.0, 100.0], colour=[0, 0, 0, 1], size=[0.0, 0.0])
        ),
    )


@pytest.fixture(scope="class")
def test_frame() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.FRAME),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=PictureMessage(
            data=LineData(
                line=[10.0, 20.0, 50.0, 20.0, 50.0, 100.0, 10.0, 100.0, 10.0, 20.0],
                colour=[0, 0, 0, 1],
                width=2,
            )
        ),
    )


@pytest.fixture(scope="class")
def test_data(
    request,
    test_rectangle: Message,
    test_line: Message,
    test_frame: Message,
) -> None:
    request.cls.test_circle = test_line
    request.cls.test_rectangle = test_rectangle
    request.cls.test_line = test_line
    request.cls.test_frame = test_frame


@pytest.mark.usefixtures("test_data")
class BasicDrawingTestCase(GraphicUnitTest):

    def test_drawing_circular_canvas(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.circle = True
        canvas.pos = (0, 0)
        canvas.tool = Tools.LINE.value
        touch = UnitTestTouch(x=200, y=200)
        touch.touch_down()
        touch.touch_move(x=100, y=100)
        touch.touch_up()
        colour = canvas.colour
        expected_line = [200.0, 200.0, 100.0, 100.0]
        assert json.loads(wb_screen.message) == {
            "topic": self.test_line.topic.dict(),
            "username": self.test_line.username,
            "game_id": root_widget.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.message)["value"]["draw_id"],
                "data": {
                    "line": expected_line,
                    "colour": colour,
                    "width": 2,
                },
            },
        }
        self.advance_frames(2)
        canvas.circle = False
        assert Tools.LINE.value in touch.ud
        assert isinstance(touch.ud[Tools.LINE.value], Line)
        assert touch.ud[Tools.LINE.value].points == expected_line

    def test_drawing_line(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.pos = (0, 0)
        canvas.tool = Tools.LINE.value
        touch = UnitTestTouch(x=200, y=200)
        touch.touch_down()
        touch.touch_move(x=100, y=100)
        touch.touch_up()
        colour = canvas.colour
        expected_line = [200.0, 200.0, 100.0, 100.0]
        assert json.loads(wb_screen.message) == {
            "topic": self.test_line.topic.dict(),
            "username": self.test_line.username,
            "game_id": root_widget.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.message)["value"]["draw_id"],
                "data": {
                    "line": expected_line,
                    "colour": colour,
                    "width": 2,
                },
            },
        }
        self.advance_frames(2)
        assert Tools.LINE.value in touch.ud
        assert isinstance(touch.ud[Tools.LINE.value], Line)
        assert touch.ud[Tools.LINE.value].points == expected_line

    def test_drawing_frame(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.tool = Tools.FRAME.value
        canvas.pos = (0, 0)
        touch = UnitTestTouch(200, 200)
        touch.touch_down()
        touch.touch_move(x=10, y=100)
        touch.touch_move(x=50, y=20)
        touch.touch_up()
        colour = canvas.colour
        assert json.loads(wb_screen.message) == {
            "topic": self.test_frame.topic.dict(),
            "username": self.test_frame.username,
            "game_id": root_widget.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.message)["value"]["draw_id"],
                "data": {
                    "line": self.test_frame.value.data.line,
                    "colour": colour,
                    "width": 2,
                },
            },
        }
        self.advance_frames(2)
        assert Tools.FRAME.value in touch.ud
        assert isinstance(touch.ud[Tools.FRAME.value], Line)
        assert touch.ud[Tools.FRAME.value].points == self.test_frame.value.data.line

    def test_drawing_rectangle(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.tool = Tools.RECT.value
        canvas.pos = (0, 0)
        touch = UnitTestTouch(x=200, y=200)
        touch.touch_down()
        touch.touch_move(x=100, y=100)
        touch.touch_up()
        colour = canvas.colour
        assert json.loads(wb_screen.message) == {
            "topic": self.test_rectangle.topic.dict(),
            "username": self.test_rectangle.username,
            "game_id": root_widget.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.message)["value"]["draw_id"],
                "data": {
                    "colour": colour,
                    "pos": self.test_rectangle.value.data.pos,
                    "size": self.test_rectangle.value.data.size,
                },
            },
        }
        self.advance_frames(2)
        assert Tools.RECT.value in touch.ud
        assert isinstance(touch.ud[Tools.RECT.value], Rectangle)
        assert (
            list(touch.ud[Tools.RECT.value].pos) == self.test_rectangle.value.data.pos
        )
        assert (
            list(touch.ud[Tools.RECT.value].size) == self.test_rectangle.value.data.size
        )

    def test_drawing_line_from_websocket(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_line = self.test_line.copy(deep=True)
        incoming_line.username = "New user"
        wb_screen.received = incoming_line.json()
        assert json.loads(wb_screen.received_raw) == incoming_line.dict()

        draw_id = incoming_line.value.draw_id
        line = getattr(wb_screen.ids, draw_id)
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
        wb_screen.received = incoming_rectangle.json()
        assert json.loads(wb_screen.received_raw) == incoming_rectangle.dict()

        draw_id = incoming_rectangle.value.draw_id
        rect = getattr(wb_screen.ids, draw_id)
        assert list(rect.pos) == incoming_rectangle.value.data.pos
        assert list(rect.size) == incoming_rectangle.value.data.size

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_drawing_frame_from_websocket(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_line = self.test_frame.copy(deep=True)
        incoming_line.username = "New user"
        wb_screen.received = incoming_line.json()
        assert json.loads(wb_screen.received_raw) == incoming_line.dict()

        draw_id = incoming_line.value.draw_id
        line = getattr(wb_screen.ids, draw_id)
        assert line.points == incoming_line.value.data.line

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
