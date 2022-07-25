from typing import Optional

from fastapi import FastAPI, Path, WebSocket
from starlette.websockets import WebSocketDisconnect

from codejam.server.connection_manager import ConnectionManager
from codejam.server.game import Game
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import DrawOperations, TopicEnum
from codejam.server.user import User

app = FastAPI(title="WebSocket Example")

manager = ConnectionManager()


@app.websocket("/ws/{username}/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket, username: str, game_id: Optional[str] = Path(None)
):
    """Websocket Endpoint"""
    print("Accepting client connection...")
    user = User(username=username, websocket=websocket)
    if game_id not in manager.active_games:
        manager.active_games[game_id] = Game(creator=user, secret=game_id)
    await manager.join_game(game_id=game_id, new_member=user)
    try:
        while True:
            data = await websocket.receive_json()
            print("received: " + str(data))
            parsed_data = Message(**data)
            # TODO: Extract handlers out of endpoint
            if (
                parsed_data
                and parsed_data.topic.type == TopicEnum.DRAW.value
                and parsed_data.topic.operation == DrawOperations.LINE.value
            ):
                await manager.broadcast(
                    game_id=game_id,
                    message=parsed_data,
                )
    except WebSocketDisconnect:
        manager.leave(game_id=game_id, member=user)
