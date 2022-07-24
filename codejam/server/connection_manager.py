from typing import Dict, List

from starlette.websockets import WebSocket


class ConnectionManager:
    """Manages web socket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.ids = []

    async def connect(self, websocket: WebSocket):
        """Accepts the connections and stores it in a list"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove the connections from active connections"""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        """Broadcast the message to all active clients"""
        for connection in self.active_connections:
            await connection.send_json(message)
