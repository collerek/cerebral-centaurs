from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    TopicEnum,
)


def test_wrong_operation_per_topic(test_client: str, test_data: Message):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        test_data.topic.type = TopicEnum.CHAT
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == {
            "game_id": None,
            "topic": {"operation": "BROADCAST", "type": "ERROR"},
            "username": "client",
            "value": {
                "error_id": data["value"]["error_id"],
                "exception": "ValidationError",
                "value": "2 validation errors for Message\n"
                "topic -> operation\n"
                "  Not allowed operations for CHAT (type=value_error)\n"
                "value\n"
                "  Invalid topic type and operation provided! "
                "(type=value_error)",
            },
        }


def test_drawing_before_joining_raises_exception(test_client: str, test_data: Message):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == {
            "game_id": None,
            "topic": {"operation": "BROADCAST", "type": "ERROR"},
            "username": "client",
            "value": {
                "error_id": data["value"]["error_id"],
                "exception": "GameNotStarted",
                "value": "You have to join or create a game before you can draw",
            },
        }


def test_wrong_message_for_topic_raises_exception(
    test_client: str, test_data: Message, chat_message: Message
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        test_data.value = chat_message.value
        websocket.send_json(test_data.dict())
        data = websocket.receive_json()
        assert data == {
            "game_id": None,
            "topic": {"operation": "BROADCAST", "type": "ERROR"},
            "username": "client",
            "value": {
                "error_id": data["value"]["error_id"],
                "exception": "ValidationError",
                "value": "1 validation error for Message\n"
                "value\n"
                "  Not allowed message value for DRAW (type=value_error)",
            },
        }
