import json

import pytest
from kivy.base import EventLoop
from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.uix.screenmanager import NoTransition

from codejam.client.client import root_widget
from codejam.client.widgets.chat_window import Chat
from codejam.client.widgets.draw_canvas import Tools
from codejam.server.interfaces.chat_message import ChatMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    ChatOperations,
    Topic,
    TopicEnum,
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
def test_data(
    request,
    test_chat_message: Message,
) -> None:
    request.cls.test_message = test_chat_message


@pytest.mark.usefixtures("test_data")
class ChatTestCase(GraphicUnitTest):

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

        assert json.loads(wb_screen.message) == {
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

    def test_adding_chat_message_from_websocket(self, *args):
        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        incoming_message = self.test_message.copy(deep=True)
        incoming_message.username = "New user"
        incoming_message.value.message = "Websocket message"
        wb_screen.received = incoming_message.json()
        assert json.loads(wb_screen.received_raw) == incoming_message.dict()

        self.advance_frames(2)
        first_message = wb_screen.ids.chat_window.ids.chat_box.children[0]
        assert isinstance(first_message, Chat)
        assert first_message.message == incoming_message.value.message
        assert first_message.sender == incoming_message.value.sender
