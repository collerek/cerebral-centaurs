import pytest
from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.exceptions import UserAlreadyExists
from codejam.server.interfaces.message import Message


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

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            game_join_message.game_id = game_id
            websocket2.send_json(game_join_message.dict())
            game_joined = websocket2.receive_json()
            joined_message = Message(**game_joined)
            assert joined_message.value.game_id == game_id
            assert joined_message.value.success
            data = websocket2.receive_json()
            assert data == test_data.dict()


def test_ending_game(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    game_creation_message: Message,
    game_join_message: Message,
    game_end_message: Message,
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(game_creation_message.dict())
        game_created = websocket.receive_json()
        created_mesage = Message(**game_created)
        game_id = created_mesage.value.game_id
        game_end_message.game_id = game_id

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            game_join_message.game_id = game_id
            websocket2.send_json(game_join_message.dict())
            websocket2.receive_json()
            websocket.send_json(game_end_message.dict())
            data = websocket2.receive_json()
            assert data == {
                "game_id": game_id,
                "topic": {"operation": "BROADCAST", "type": "ERROR"},
                "username": "client",
                "value": {
                    "error_id": data["value"]["error_id"],
                    "exception": "GameEnded",
                    "value": "Game was ended by the creator!",
                },
            }


def test_ending_not_existing(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    game_creation_message: Message,
    game_join_message: Message,
    game_end_message: Message,
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        game_end_message.game_id = "dummy_game_id"
        websocket.send_json(game_end_message.dict())
        data = websocket.receive_json()
        assert data == {
            "game_id": "dummy_game_id",
            "topic": {"operation": "BROADCAST", "type": "ERROR"},
            "username": "client",
            "value": {
                "error_id": data["value"]["error_id"],
                "exception": "GameNotExist",
                "value": "Game with id: dummy_game_id does not exist!",
            },
        }


def test_joining_with_existing_username_raises_error(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    game_creation_message: Message,
    game_join_message: Message,
):
    client = TestClient(app)
    with pytest.raises(UserAlreadyExists):
        with client.websocket_connect(f"/ws/{test_client}"):
            with client.websocket_connect(f"/ws/{test_client}"):
                pass  # pragma: no cover
