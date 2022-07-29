import json

import pytest
from kivy.base import EventLoop
from kivy.factory import Factory
from kivy.graphics import Line, Rectangle
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget
from codejam.client.widgets.chatwindow import Chat
from codejam.client.widgets.drawcanvas import Tools
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
)
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
def test_error() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.ERROR, operation=ErrorOperations.BROADCAST),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=ErrorMessage(exception="TestExp", value="Test"),
    )


@pytest.fixture(scope="class")
def test_chat_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.CHAT, operation=ChatOperations.SAY),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=ChatMessage(sender=root_widget.username, message="Test message"),
    )


@pytest.fixture(scope="class")
def game_start_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.START),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=GameMessage(success=True, game_id=root_widget.game_id),
    )


@pytest.fixture(scope="class")
def game_creation_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.CREATE),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=GameMessage(success=True, game_id="newID"),
    )


@pytest.fixture(scope="class")
def game_turn_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.TURN),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=GameMessage(
            success=True,
            game_id=root_widget.game_id,
            turn=TurnMessage(
                turn_no=1,
                active=True,
                drawer=root_widget.username,
                duration=1,
                level=PhraseDifficulty.MEDIUM,
                score={root_widget.username: 100},
                phrase="Dummy",
            ),
        ),
    )


@pytest.fixture(scope="class")
def game_win_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.WIN),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=GameMessage(
            success=True,
            game_id=root_widget.game_id,
            turn=TurnMessage(
                turn_no=1,
                active=True,
                winner=root_widget.username,
                duration=1,
                level=PhraseDifficulty.MEDIUM,
                score={root_widget.username: 100},
                phrase="Dummy",
            ),
        ),
    )


@pytest.fixture(scope="class")
def test_data(
    request,
    test_error: Message,
    test_rectangle: Message,
    test_line: Message,
    test_frame: Message,
    test_chat_message: Message,
    game_start_message: Message,
    game_creation_message: Message,
    game_turn_message: Message,
    game_win_message: Message,
) -> None:
    request.cls.test_error = test_error
    request.cls.test_rectangle = test_rectangle
    request.cls.test_line = test_line
    request.cls.test_frame = test_frame
    request.cls.test_message = test_chat_message
    request.cls.game_start_message = game_start_message
    request.cls.game_create_message = game_creation_message
    request.cls.game_turn_message = game_turn_message
    request.cls.game_win_message = game_win_message


@pytest.mark.usefixtures("test_data")
class BasicDrawingTestCase(GraphicUnitTest):
    def test_restarting_game(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.create_room = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        self.advance_frames(1)
        wb_screen.start_game()
        self.root.current = "menu_screen"
        print("re-enter")
        self.advance_frames(2)
        self.root.current = "whiteboard"
        self.advance_frames(2)
        assert "lobby" in self.root.ids
        assert isinstance(self.root.ids["lobby"], Factory.Lobby)

    def test_adding_chat_message(self, *args):
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
        canvas.tool = Tools.LINE.value

        wb_screen.ids.chat_window.ids.message_input.text = "Test message"
        button = wb_screen.ids.chat_window.ids.chat_button
        touch = UnitTestTouch(x=button.center_x, y=button.center_y)
        touch.touch_down()
        touch.touch_up()

        assert json.loads(wb_screen.wb.message) == {
            "topic": self.test_message.topic.dict(),
            "username": self.test_message.username,
            "game_id": self.test_message.game_id,
            "value": self.test_message.value.dict(),
        }
        self.advance_frames(2)
        first_message = wb_screen.ids.chat_window.ids.chat_box.children[0]
        assert isinstance(first_message, Chat)
        assert first_message.message == self.test_message.value.message
        assert first_message.sender == self.test_message.value.sender

        wb_screen.ids.chat_window.ids.message_input.text = "Test message 2"
        button = wb_screen.ids.chat_window.ids.chat_button
        touch = UnitTestTouch(x=button.center_x, y=button.center_y)
        touch.touch_down()
        touch.touch_up()
        self.advance_frames(2)

        second_message = wb_screen.ids.chat_window.ids.chat_box.children[0]
        assert isinstance(second_message, Chat)
        assert second_message.message == "Test message 2"
        assert second_message.sender == self.test_message.value.sender

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
        assert json.loads(wb_screen.wb.message) == {
            "topic": self.test_line.topic.dict(),
            "username": self.test_line.username,
            "game_id": self.test_line.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.wb.message)["value"]["draw_id"],
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
        assert json.loads(wb_screen.wb.message) == {
            "topic": self.test_frame.topic.dict(),
            "username": self.test_frame.username,
            "game_id": self.test_frame.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.wb.message)["value"]["draw_id"],
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
        assert json.loads(wb_screen.wb.message) == {
            "topic": self.test_rectangle.topic.dict(),
            "username": self.test_rectangle.username,
            "game_id": self.test_rectangle.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.wb.message)["value"]["draw_id"],
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

    def test_adding_chat_message_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.test_message.copy(deep=True)
        incoming_message.username = "New user"
        incoming_message.value.message = "Websocket message"
        wb_screen.wb.received = incoming_message.json()
        assert json.loads(wb_screen.wb.btn_text) == incoming_message.dict()

        self.advance_frames(2)
        first_message = wb_screen.ids.chat_window.ids.chat_box.children[0]
        assert isinstance(first_message, Chat)
        assert first_message.message == incoming_message.value.message
        assert first_message.sender == incoming_message.value.sender

    def test_creating_game_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.game_create_message.copy(deep=True)
        wb_screen.wb.received = incoming_message.json()
        assert json.loads(wb_screen.wb.btn_text) == incoming_message.dict()

        self.advance_frames(2)
        assert wb_screen.game_id == incoming_message.value.game_id

    def test_starting_game_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.game_start_message.copy(deep=True)
        wb_screen.wb.received = incoming_message.json()
        assert json.loads(wb_screen.wb.btn_text) == incoming_message.dict()

        self.advance_frames(2)
        assert wb_screen.game_active

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

        draw_id = incoming_line.value.draw_id
        line = getattr(wb_screen.wb.ids, draw_id)
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

        draw_id = incoming_rectangle.value.draw_id
        rect = getattr(wb_screen.wb.ids, draw_id)
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
        wb_screen.wb.received = incoming_line.json()
        assert json.loads(wb_screen.wb.btn_text) == incoming_line.dict()

        draw_id = incoming_line.value.draw_id
        line = getattr(wb_screen.wb.ids, draw_id)
        assert line.points == incoming_line.value.data.line

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

    def test_playing_turn(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.wb.received = self.game_turn_message.json()
        assert json.loads(wb_screen.wb.btn_text) == self.game_turn_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == "Now is your turn to draw!"
        assert (
            popup.message
            == f"You have {self.game_turn_message.value.turn.duration} seconds to draw!"
        )

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_winning_turn(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.wb.received = self.game_win_message.json()
        assert json.loads(wb_screen.wb.btn_text) == self.game_win_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.header == "You WON!"
        assert popup.message == self.game_win_message.value.turn.phrase
        assert popup.additional_message == "Next turn will start in 5 seconds!"

        popup.dismiss()
        self.advance_frames(10)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
