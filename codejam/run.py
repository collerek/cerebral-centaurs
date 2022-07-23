from typing import Dict, List

from fastapi import FastAPI, WebSocket

# Create application
from starlette.websockets import WebSocketDisconnect

app = FastAPI(title="WebSocket Example")


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


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """WebSocket Endpoint"""  # noqa: D403
    print("Accepting client connection...")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast({"client_id": client_id, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
