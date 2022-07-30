import pytest

from codejam.server.interfaces.chat_message import ChatMessage
from codejam.server.interfaces.game_message import GameMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage, RectData
from codejam.server.interfaces.topics import (
    ChatOperations, DrawOperations,
    GameOperations,
    Topic,
    TopicEnum,
)
from tests.unit.test_client.mocks import WebsocketMock


@pytest.fixture
def test_client() -> str:
    return "client"


@pytest.fixture
def second_test_client() -> str:
    return "client2"


@pytest.fixture
def test_data(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
        username=test_client,
        game_id=None,
        value=PictureMessage(
            data=LineData(line=[0, 1, 1, 1], colour=[0, 0, 0, 1], width=2)
        ),
    )


@pytest.fixture
def test_frame(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.FRAME),
        username=test_client,
        game_id=None,
        value=PictureMessage(
            data=LineData(
                line=[10.0, 20.0, 50.0, 20.0, 50.0, 100.0, 10.0, 100.0, 10.0, 20.0],
                colour=[0, 0, 0, 1],
                width=2,
            )
        ),
    )

@pytest.fixture
def test_rect(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.RECT),
        username=test_client,
        game_id=None,
        value=PictureMessage(
            data=RectData(pos=[100.0, 100.0], colour=[0, 0, 0, 1], size=[0.0, 0.0])
        ),
    )


@pytest.fixture
def game_creation_message(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.CREATE),
        username=test_client,
        game_id=None,
        value=GameMessage(
            success=False,
            game_id="",
            turn=None
        ),
    )


@pytest.fixture
def game_join_message(second_test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.JOIN),
        username=second_test_client,
        game_id=None,
        value=None,
    )


@pytest.fixture
def game_end_message(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.END),
        username=test_client,
        game_id=None,
        value=None,
    )


@pytest.fixture
def game_start_message(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.START),
        username=test_client,
        game_id=None,
        value=None,
    )

@pytest.fixture
def game_leave_message(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.LEAVE),
        username=test_client,
        game_id=None,
        value=None,
    )

@pytest.fixture
def chat_message(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.CHAT, operation=ChatOperations.SAY),
        username=test_client,
        game_id=None,
        value=ChatMessage(sender=test_client, message="test_message"),
    )

@pytest.fixture()
def mocked_websockets(mocker):
    web_socket_mock = WebsocketMock()
    mocker.patch("codejam.client.widgets.whiteboard_screen.websockets", web_socket_mock)
    return web_socket_mock
