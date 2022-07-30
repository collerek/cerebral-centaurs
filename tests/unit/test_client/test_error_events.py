import json

import pytest
from kivy.base import EventLoop
from kivy.tests.common import GraphicUnitTest
from kivy.uix.modalview import ModalView

from codejam.client.client import root_widget
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    ErrorOperations,
    Topic,
    TopicEnum,
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
def test_data(
        request,
        test_error: Message,
) -> None:
    request.cls.test_error = test_error


@pytest.mark.usefixtures("test_data")
class ErrorTestCase(GraphicUnitTest):

    def test_displaying_error(self, *args):
        EventLoop.ensure_window()
        self._win = EventLoop.window

        self.root_widget = root_widget
        self.render(self.root_widget)
        wb_screen = self.root_widget.get_screen("whiteboard")

        wb_screen.received = self.test_error.json()
        assert json.loads(wb_screen.received_raw) == self.test_error.dict()

        popup = next((x for x in self._win.children if isinstance(x, ModalView)), None)
        assert popup.title == self.test_error.value.exception
        assert popup.message == self.test_error.value.value

        popup.dismiss()
        self.advance_frames(1)

        self.render(self.root_widget)
        self.assertLess(len(self._win.children), 2)
