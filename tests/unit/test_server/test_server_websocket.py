import pydantic
import pytest
from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.picture_message import LineData, PictureMessage
from codejam.server.interfaces.topics import DrawOperations, Topic, TopicEnum


@pytest.fixture
def test_client() -> str:
    return "client"


@pytest.fixture
def second_test_client() -> str:
    return "client2"


@pytest.fixture
def test_game() -> str:
    return "random"


@pytest.fixture
def test_data(test_client: str, test_game: str) -> Message:
    return Message(
        topic=Topic(type=TopicEnum.DRAW, operation=DrawOperations.LINE),
        username=test_client,
        game_id=test_game,
        value=PictureMessage(data=LineData(line=[0, 1, 1, 1], colour=[0, 0, 0, 1])),
    )


def test_basic_line_draw(test_client: str, test_game: str, test_data: Message):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}/{test_game}") as websocket:
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == test_data.dict()


def test_joining_player_receive_history(
    test_client: str, second_test_client: str, test_game: str, test_data: Message
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}/{test_game}") as websocket:
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == test_data.dict()

    with client.websocket_connect(f"/ws/{second_test_client}/{test_game}") as websocket:
        data = websocket.receive_json()
        assert data == test_data.dict()


def test_wrong_operation_per_topic(test_client: str, test_game: str, test_data: Message):
    client = TestClient(app)
    with pytest.raises(pydantic.ValidationError) as e:
        with client.websocket_connect(f"/ws/{test_client}/{test_game}") as websocket:
            test_data.topic.type = TopicEnum.CHAT
            websocket.send_json(test_data.dict())
    assert "Not allowed operations for CHAT" in str(e)
