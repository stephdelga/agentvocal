import os, json, base64, asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Connect

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL      = os.getenv("RAILWAY_URL")

OPENAI_WS = "wss://api.openai.com/v1/realtime?model=speech-s2s-1"
print(f"🚀 RAILWAY_URL = {RAILWAY_URL}")
print(f"🚀 OPENAI_API_KEY present? {'yes' if OPENAI_API_KEY else 'no'}")

app = FastAPI()

@app.post("/incoming-call")
async def incoming_call(request: Request):
    resp = VoiceResponse()
    conn = Connect()
    conn.stream(url=f"wss://{RAILWAY_URL}/media-stream")
    resp.append(conn)
    return Response(content=str(resp), media_type="application/xml")

@app.websocket("/media-stream")
async def media_stream(ws: WebSocket):
    await ws.accept()
    print("→ connexion Twilio OK")

    # ouvrir le WebSocket vers OpenAI
    openai_ws = await websockets.connect(
        OPENAI_WS,
        extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
    )
    await openai_ws.send(json.dumps({"kind": "session_start"}))
    print("→ session OpenAI démarrée")

    async def relay_to_openai():
        try:
            while True:
                data = json.loads(await ws.receive_text())
                if data["event"] == "media":
                    audio = base64.b64decode(data["media"]["payload"])
                    await openai_ws.send(audio)
                elif data["event"] == "stop":
                    break
        finally:
            await openai_ws.send(json.dumps({"kind": "session_end"}))

    async def relay_to_twilio():
        try:
            while True:
                chunk = await openai_ws.recv()
                if isinstance(chunk, bytes):
                    b64 = base64.b64encode(chunk).decode()
                    await ws.send_text(json.dumps({
                        "event": "media",
                        "media": {"payload": b64}
                    }))
                else:
                    info = json.loads(chunk)
                    if info.get("type") == "session_end":
                        break
        finally:
            pass

    await asyncio.gather(relay_to_openai(), relay_to_twilio())
    await openai_ws.close()
    await ws.close()
    print("→ connexions fermées")
