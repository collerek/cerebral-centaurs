import pydantic
import pytest
from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage
from codejam.server.interfaces.topics import (
    DrawOperations,
    GameOperations,
    Topic,
    TopicEnum,
)


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
        value=PictureMessage(data=LineData(line=[0, 1, 1, 1], colour=[0, 0, 0, 1])),
    )


@pytest.fixture
def game_creation_message(test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.CREATE),
        username=test_client,
        game_id=None,
        value=None,
    )


@pytest.fixture
def game_join_message(second_test_client: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.GAME, operation=GameOperations.JOIN),
        username=second_test_client,
        game_id=None,
        value=None,
    )


def test_basic_line_draw(
    test_client: str, test_data: Message, game_creation_message: Message
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(game_creation_message.dict())
        game_created = websocket.receive_json()
        created_mesage = Message(**game_created)
        assert created_mesage.value.success
        assert created_mesage.value.game_id is not None
        test_data.game_id = created_mesage.value.game_id
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == test_data.dict()


def test_joining_player_receive_history(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    game_creation_message: Message,
    game_join_message: Message,
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(game_creation_message.dict())
        game_created = websocket.receive_json()
        created_mesage = Message(**game_created)
        game_id = created_mesage.value.game_id
        test_data.game_id = game_id
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == test_data.dict()

    with client.websocket_connect(f"/ws/{second_test_client}") as websocket:
        game_join_message.game_id = game_id
        websocket.send_json(game_join_message.dict())
        game_joined = websocket.receive_json()
        joined_message = Message(**game_joined)
        assert joined_message.value.game_id == game_id
        assert joined_message.value.success
        data = websocket.receive_json()
        assert data == test_data.dict()


def test_wrong_operation_per_topic(
    test_client: str, test_data: Message
):
    client = TestClient(app)
    with pytest.raises(pydantic.ValidationError) as e:
        with client.websocket_connect(f"/ws/{test_client}") as websocket:
            test_data.topic.type = TopicEnum.CHAT
            websocket.send_json(test_data.dict())
    assert "Not allowed operations for CHAT" in str(e)


def test_drawing_before_joining_raises_exception(
    test_client: str, test_data: Message
):
    client = TestClient(app)
    with pytest.raises(ValueError) as e:
        with client.websocket_connect(f"/ws/{test_client}") as websocket:
            websocket.send_json(test_data.dict())
    assert "You have to join or create a game before you can draw" in str(e)
