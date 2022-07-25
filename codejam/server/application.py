from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

from codejam.server.connection_manager import ConnectionManager
from codejam.server.game_controller import GameController
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import DrawOperations, TopicEnum
from codejam.server.user import User

app = FastAPI(title="WebSocket Example")

manager = ConnectionManager()


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """Websocket Endpoint"""
    print("Accepting client connection...")
    user = User(username=username, websocket=websocket)
    game_id = None
    await manager.connect(user=user)
    try:
        while True:
            data = await websocket.receive_json()
            print("received: " + str(data))
            message = Message(**data)
            # TODO: Extract handlers out of endpoint
            if (
                message
                and message.topic.type == TopicEnum.DRAW.value
                and message.topic.operation == DrawOperations.LINE.value
            ):
                if not game_id:
                    raise ValueError(
                        "You have to join or create a game " "before you can draw"
                    )
                await manager.broadcast(
                    game_id=game_id,
                    message=message,
                )
            elif message and message.topic.type == TopicEnum.GAME.value:
                controller = GameController(manager=manager)
                game_id = await controller.dispatch(message=message)
    except WebSocketDisconnect:
        manager.leave(game_id=game_id, member=user)
        manager.disconnect(user=user)
