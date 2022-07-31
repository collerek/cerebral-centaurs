import logging
from typing import cast

import pydantic
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

from codejam.server.connection_manager import ConnectionManager
from codejam.server.controllers.chat_controller import ChatController
from codejam.server.controllers.draw_controller import DrawController
from codejam.server.controllers.error_controller import ErrorController
from codejam.server.controllers.game_controller import GameController
from codejam.server.exceptions import WhiteBoardException
from codejam.server.interfaces.error_message import ErrorMessage
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ErrorOperations, Topic, TopicEnum
from codejam.server.models.user import User

app = FastAPI(title="WebSocket Example")
logger = logging.getLogger(__name__)
manager = ConnectionManager()


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """Websocket Endpoint"""
    logger.info("Accepting client connection...")
    user = User(username=username, websocket=websocket)
    game_id = None
    await manager.connect(user=user)
    controllers = {
        TopicEnum.DRAW.value: DrawController,
        TopicEnum.GAME.value: GameController,
        TopicEnum.CHAT.value: ChatController,
    }
    try:
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug("received: " + str(data))
                message = Message(**data)
                game_id = message.game_id
                controller = controllers[cast(str, message.topic.type)]
                await controller(manager=manager).dispatch(message=message)  # type: ignore
            except (pydantic.ValidationError, WhiteBoardException) as e:
                message = Message(
                    topic=Topic(type=TopicEnum.ERROR, operation=ErrorOperations.BROADCAST),
                    username=user.username,
                    game_id=game_id,
                    value=ErrorMessage(exception=e.__class__.__name__, value=str(e)),
                )
                await ErrorController(manager=manager).dispatch(message=message)
    except WebSocketDisconnect:
        pass
    finally:
        if game_id and game_id in manager.active_games:
            manager.leave(game_id=game_id, member=user)
        manager.disconnect(user=user)
