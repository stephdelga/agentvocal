from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Hello Stéphane ca va ? 👋"}

@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_bytes()
        print("Reçu :", len(data))
        await websocket.send_text("Bien reçu !")
