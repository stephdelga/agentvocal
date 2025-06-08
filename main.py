from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "hello stéphane 👋"}

@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    print("connexion web-socket établie")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            # démarrage de l'appel
            if msg.get("event") == "start":
                print("▶️ appel démarré")

            # réception des paquets audio (base64)
            elif msg.get("event") == "media":
                payload = msg["media"]["payload"]
                print(f"🎧 audio reçu (début) : {payload[:30]}...")

            # fin de l'appel
            elif msg.get("event") == "stop":
                print("⏹ appel terminé")
                break

    except Exception as e:
        print(f"erreur web-socket : {e}")

    finally:
        await websocket.close()
        print("web-socket fermé")
