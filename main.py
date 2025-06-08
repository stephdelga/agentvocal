from fastapi import FastAPI, WebSocket, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Connect
import json

app = FastAPI()

@app.get("/")
async def hello():
    return {"message": "hello stéphane 👋"}

@app.post("/incoming-call")
async def incoming_call(request: Request):
    # renvoie le TwiML qui indique à Twilio d’ouvrir le WebSocket
    resp = VoiceResponse()
    conn = Connect()
    conn.stream(url="wss://TON_DOMAINE_RAILWAY/media-stream")
    resp.append(conn)
    return Response(content=str(resp), media_type="application/xml")

@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    print("connexion WebSocket établie")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("event") == "start":
                print("▶️ appel démarré")

            elif msg.get("event") == "media":
                payload = msg["media"]["payload"]
                print(f"🎧 audio reçu (début) : {payload[:30]}...")

            elif msg.get("event") == "stop":
                print("⏹ appel terminé")
                break

    except Exception as e:
        print(f"❌ erreur WebSocket : {e}")

    finally:
        await websocket.close()
        print("🔌 WebSocket fermé")
