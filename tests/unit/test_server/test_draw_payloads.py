from starlette.testclient import TestClient

from codejam.server import app
from codejam.server.interfaces.message import Message


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


def test_basic_frame_draw(
    test_client: str, test_frame: Message, game_creation_message: Message
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(game_creation_message.dict())
        game_created = websocket.receive_json()
        created_mesage = Message(**game_created)
        assert created_mesage.value.success
        assert created_mesage.value.game_id is not None
        test_frame.game_id = created_mesage.value.game_id
        websocket.send_json(test_frame.dict())
        data = websocket.receive_json()
        assert data == test_frame.dict()


def test_basic_rectangle_draw(
    test_client: str, test_rect: Message, game_creation_message: Message
):
    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        websocket.send_json(game_creation_message.dict())
        game_created = websocket.receive_json()
        created_mesage = Message(**game_created)
        assert created_mesage.value.success
        assert created_mesage.value.game_id is not None
        test_rect.game_id = created_mesage.value.game_id
        websocket.send_json(test_rect.dict())
        data = websocket.receive_json()
        assert data == test_rect.dict()
