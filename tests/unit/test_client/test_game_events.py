import json

import pytest
from kivy.base import EventLoop
from kivy.factory import Factory
from kivy.tests.common import GraphicUnitTest
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget
from codejam.server.interfaces.game_message import GameMessage, TurnMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    GameOperations,
    Topic,
    TopicEnum,
)
from codejam.server.models.phrase_generator import PhraseDifficulty


@pytest.fixture(scope="class")
def game_start_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.START),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=GameMessage(success=True, game_id=root_widget.game_id),
    )


@pytest.fixture(scope="class")
def game_join_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.JOIN),
        username="second_user",
        game_id=root_widget.game_id,
        value=GameMessage(
            success=True,
            game_id=root_widget.game_id,
            members=[root_widget.username, "second_user"],
            game_length=10,
        ),
    )


@pytest.fixture(scope="class")
def game_leave_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.LEAVE),
        username="second_user",
        game_id=root_widget.game_id,
        value=GameMessage(
            success=True, game_id=root_widget.game_id, members=[root_widget.username]
        ),
    )


@pytest.fixture(scope="class")
def game_creation_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.CREATE),
        username=root_widget.username,
        game_id=root_widget.game_id,
        value=GameMessage(success=True, game_id="newID", game_length=5),
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
def game_end_message() -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.END),
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
    game_start_message: Message,
    game_join_message: Message,
    game_creation_message: Message,
    game_turn_message: Message,
    game_win_message: Message,
    game_leave_message: Message,
    game_end_message: Message,
) -> None:
    request.cls.game_start_message = game_start_message
    request.cls.game_create_message = game_creation_message
    request.cls.game_turn_message = game_turn_message
    request.cls.game_win_message = game_win_message
    request.cls.game_join_message = game_join_message
    request.cls.game_leave_message = game_leave_message
    request.cls.game_end_message = game_end_message


@pytest.mark.usefixtures("test_data")
class GameTestCase(GraphicUnitTest):

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
        self.advance_frames(2)
        self.root.current = "whiteboard"
        self.advance_frames(2)
        assert "lobby" in self.root.ids
        assert isinstance(self.root.ids["lobby"], Factory.Lobby)

    def test_creating_game_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.game_create_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        self.advance_frames(2)
        assert wb_screen.manager.game_id == incoming_message.value.game_id

    def test_starting_game_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.game_start_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        self.advance_frames(2)
        assert wb_screen.manager.game_active

    def test_joining_and_leaving_game_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.game_join_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        self.advance_frames(2)
        assert len(wb_screen.ids.score_board.ids.scores.children) == 2

        incoming_message = self.game_leave_message.copy(deep=True)
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        self.advance_frames(2)
        assert len(wb_screen.ids.score_board.ids.scores.children) == 1







    def test_playing_turn(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.received = self.game_turn_message.json()
        assert json.loads(wb_screen.received_raw) == self.game_turn_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == "Now is your turn to draw!"
        assert (
            popup.message
            == f"You have {self.game_turn_message.value.turn.duration} seconds to draw!"
        )

        popup.dismiss()
        self.advance_frames(1)
        assert wb_screen.ids.counter.text != "WAITING FOR START"
        assert int(wb_screen.ids.counter.text) <= 60

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_winning_turn(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.received = self.game_win_message.json()
        assert json.loads(wb_screen.received_raw) == self.game_win_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.header == "You WON!"
        assert popup.message == self.game_win_message.value.turn.phrase
        assert popup.additional_message == "Next turn will start in 5 seconds!"

        popup.dismiss()
        self.advance_frames(10)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)

    def test_ending_game(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.received = self.game_end_message.json()
        assert json.loads(wb_screen.received_raw) == self.game_end_message.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.header == "GAME END!"
        assert popup.title == "The winner is:"
        assert popup.message == self.game_end_message.username

        popup.dismiss()
        self.advance_frames(10)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
