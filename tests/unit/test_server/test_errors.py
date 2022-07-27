from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import (
    GameOperations,
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


def test_starting_game_by_not_creator_raises_exception(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    game_creation_message: Message,
    game_join_message: Message,
    game_start_message: Message,
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

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            game_join_message.game_id = game_id
            websocket2.send_json(game_join_message.dict())
            joined_message = Message(**websocket2.receive_json())
            assert joined_message.topic.operation == GameOperations.JOIN.value
            websocket2.receive_json()
            game_start_message.game_id = game_id
            game_start_message.username = second_test_client
            websocket2.send_json(game_start_message.dict())
            data = websocket2.receive_json()
            assert data == {
                "game_id": game_id,
                "topic": {"operation": "BROADCAST", "type": "ERROR"},
                "username": "client2",
                "value": {
                    "error_id": data["value"]["error_id"],
                    "exception": "CannotStartNotOwnGame",
                    "value": f"Only client can start the game {game_id}",
                },
            }
