from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.interfaces.message import Message


def test_basic_chat_message(
    test_client: str, game_creation_message: Message, chat_message: Message
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(game_creation_message.dict())
        game_created = websocket.receive_json()
        created_mesage = Message(**game_created)
        assert created_mesage.value.game_id is not None
        chat_message.game_id = created_mesage.value.game_id
        websocket.send_json(chat_message.dict())
        data = websocket.receive_json()
        assert data == chat_message.dict()
