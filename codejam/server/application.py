from fastapi import FastAPI, WebSocket

# Create application
from starlette.websockets import WebSocketDisconnect

from codejam.server.connection_manager import ConnectionManager

app = FastAPI(title="WebSocket Example")

manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """WebSocket Endpoint"""  # noqa: D403
    print("Accepting client connection...")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            await manager.broadcast({"client_id": client_id, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
