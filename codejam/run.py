from fastapi import FastAPI, WebSocket

# Create application
app = FastAPI(title="WebSocket Example")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket Endpoint"""  # noqa: D403
    print("Accepting client connection...")
    await websocket.accept()
    while True:
        try:
            info = await websocket.receive_text()
            if info:
                await websocket.send_json(info)
        except Exception as e:
            print("error:", e)
            break
