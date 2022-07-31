import json
import time

import pytest
from kivy.base import EventLoop
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget
from codejam.client.widgets.draw_canvas import Tools
from codejam.server.interfaces.game_message import GameMessage, TurnMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    DrawOperations, GameOperations, Topic,
    TopicEnum, TrickOperations,
)
from codejam.server.interfaces.trick_message import TrickMessage
from codejam.server.models.phrase_generator import PhraseDifficulty


@pytest.fixture(scope="class")
def test_trick_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.TRICK, operation=TrickOperations.NOTHING),
        username="Dirty Goblin",
        game_id=root_widget.game_id,
        value=TrickMessage(game_id=root_widget.game_id, description="Test trick"),
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
def test_data(
    request,
    test_trick_message: Message,
game_turn_message: Message
) -> None:

    request.cls.test_trick_message = test_trick_message
    request.cls.game_turn_message = game_turn_message




@pytest.mark.usefixtures("test_data")
class TricksTestCase(GraphicUnitTest):

    def test_trick_nothing(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.received = self.test_trick_message.json()
        assert json.loads(wb_screen.received_raw) == self.test_trick_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == self.test_trick_message.topic.operation
        assert popup.message == self.test_trick_message.value.description

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_trick_landslide(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        initial_offset_x = wb_screen.cvs.offset_x
        initial_offset_y = wb_screen.cvs.offset_y

        incoming_message = self.test_trick_message.copy(deep=True)
        incoming_message.topic.operation = TrickOperations.LANDSLIDE
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == incoming_message.topic.operation.value
        assert popup.message == self.test_trick_message.value.description

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
        self.advance_frames(50)

        assert wb_screen.cvs.offset_x != initial_offset_x
        assert wb_screen.cvs.offset_y != initial_offset_y
        assert wb_screen.cvs.angle != 0

        incoming_message = self.game_turn_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        assert not wb_screen.current_trick._widgets
        assert wb_screen.cvs.offset_x == initial_offset_x
        assert wb_screen.cvs.offset_y == initial_offset_y
        assert wb_screen.cvs.angle == 0

    def test_trick_pacman(self, *args):
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

        incoming_message = self.test_trick_message.copy(deep=True)
        incoming_message.topic.operation = TrickOperations.PACMAN
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == incoming_message.topic.operation.value
        assert popup.message == self.test_trick_message.value.description

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root)
        self.assertLess(len(self._win.children), 2)
        self.advance_frames(5)

        assert json.loads(wb_screen.second_message) == {
            "topic": Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE).dict(),
            "username": root_widget.username,
            "game_id": root_widget.game_id,
            "value": {
                "draw_id": json.loads(wb_screen.second_message)["value"]["draw_id"],
                "data": {
                    "line": json.loads(wb_screen.second_message)["value"]["data"]["line"],
                    "colour": [.2, .9, .5],
                    "width": 15,
                },
            },
        }
        wb_screen.cancel_trick()
        self.advance_frames(300)

    def test_trick_earthquake(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        initial_offset_x = wb_screen.cvs.offset_x
        initial_offset_y = wb_screen.cvs.offset_y

        incoming_message = self.test_trick_message.copy(deep=True)
        incoming_message.topic.operation = TrickOperations.EARTHQUAKE
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == incoming_message.topic.operation.value
        assert popup.message == self.test_trick_message.value.description

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
        self.advance_frames(50)
        assert wb_screen.cvs.offset_x != initial_offset_x
        assert wb_screen.cvs.offset_y != initial_offset_y

        incoming_message = self.game_turn_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        assert not wb_screen.current_trick._widgets
        assert wb_screen.cvs.offset_x == initial_offset_x
        assert wb_screen.cvs.offset_y == initial_offset_y
        assert wb_screen.cvs.angle == 0

    def test_trick_snail(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.test_trick_message.copy(deep=True)
        incoming_message.topic.operation = TrickOperations.SNAIL
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == incoming_message.topic.operation.value
        assert popup.message == self.test_trick_message.value.description

        popup.dismiss()
        self.advance_frames(1)

        assert wb_screen.snail_active

        self.root = root_widget
        self.root.can_draw = True
        self.render(self.root)
        self.root.transition = NoTransition()
        self.root.ws = True
        self.root.current = "whiteboard"
        wb_screen = self.root.current_screen
        wb_screen.message = ""
        self.advance_frames(1)

        canvas = wb_screen.ids.canvas
        canvas.pos = (0, 0)
        canvas.tool = Tools.LINE.value
        assert wb_screen.snail_active
        touch = UnitTestTouch(x=300, y=300)
        touch.touch_down()
        touch.touch_move(x=200, y=200)
        touch.touch_move(x=300, y=300)
        touch.touch_move(x=400, y=400)
        time.sleep(1)
        touch.touch_move(x=250, y=250)
        touch.touch_up()
        self.advance_frames(50)
        self.render(self.root)
        assert wb_screen.snail_active
        colour = canvas.colour
        expected_line = [300.0, 300.0, 200.0, 200.0, 250.0, 250.0]
        assert json.loads(wb_screen.message) == {
            "topic": Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
            "username": root_widget.username,
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

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
        incoming_message = self.game_turn_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        assert not wb_screen.snail_active
