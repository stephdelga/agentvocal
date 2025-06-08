import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request, Response

# Variables d'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL")
OPENAI_WS = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

print(f"🚀 RAILWAY_URL = {RAILWAY_URL}")
print(f"🚀 OPENAI_API_KEY present? {'yes' if OPENAI_API_KEY else 'no'}")

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Serveur Twilio + OpenAI Realtime actif"}

@app.post("/incoming-call")
def incoming_call():
    """Twilio redirige l'appel vers notre WebSocket"""
    print("📞 Appel reçu - redirection vers WebSocket")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{RAILWAY_URL}/media-stream" />
    </Connect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.websocket("/media-stream")
async def media_stream(ws: WebSocket):
    """WebSocket qui connecte Twilio à OpenAI"""
    await ws.accept()
    print("🔌 Connexion WebSocket Twilio établie")
    
    try:
        # Connexion à OpenAI Realtime
        openai_ws = await websockets.connect(
            OPENAI_WS,
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        )
        print("🤖 Connexion OpenAI Realtime établie")
        
        # Configuration de la session OpenAI
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """Tu es un assistant vocal français intelligent et amical. 
                Tu aides les clients avec leurs questions.
                Réponds de manière naturelle et conversationnelle.
                Sois concis mais informatif.""",
                "voice": "alloy",
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                }
            }
        }
        await openai_ws.send(json.dumps(session_config))
        print("⚙️ Configuration OpenAI envoyée")
        
        async def handle_twilio_messages():
            """Gère les messages venant de Twilio"""
            try:
                async for message in ws.iter_text():
                    data = json.loads(message)
                    
                    if data.get("event") == "media":
                        # Audio de l'utilisateur -> OpenAI
                        audio_payload = data["media"]["payload"]
                        audio_data = base64.b64decode(audio_payload)
                        
                        audio_event = {
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(audio_data).decode()
                        }
                        await openai_ws.send(json.dumps(audio_event))
                    
                    elif data.get("event") == "start":
                        print("🎙️ Stream audio démarré")
                        
                    elif data.get("event") == "stop":
                        print("⏹️ Stream audio arrêté")
                        break
                        
            except Exception as e:
                print(f"❌ Erreur Twilio: {e}")
        
        async def handle_openai_messages():
            """Gère les messages venant d'OpenAI"""
            try:
                async for message in openai_ws:
                    data = json.loads(message)
                    
                    if data.get("type") == "response.audio.delta":
                        # Audio d'OpenAI -> Twilio
                        audio_data = data.get("delta", "")
                        if audio_data:
                            media_message = {
                                "event": "media",
                                "streamSid": "stream_sid_placeholder",
                                "media": {
                                    "payload": audio_data
                                }
                            }
                            await ws.send_text(json.dumps(media_message))
                    
                    elif data.get("type") == "input_audio_buffer.speech_started":
                        print("🗣️ Utilisateur commence à parler")
                        
                    elif data.get("type") == "input_audio_buffer.speech_stopped":
                        print("🤐 Utilisateur arrête de parler")
                        
                    elif data.get("type") == "conversation.item.input_audio_transcription.completed":
                        transcript = data.get("transcript", "")
                        print(f"📝 Transcription: {transcript}")
                        
                    elif data.get("type") == "response.text.delta":
                        text_delta = data.get("delta", "")
                        print(f"💬 Réponse: {text_delta}", end="")
                        
            except Exception as e:
                print(f"❌ Erreur OpenAI: {e}")
        
        # Lancer les deux gestionnaires en parallèle
        await asyncio.gather(
            handle_twilio_messages(),
            handle_openai_messages()
        )
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        try:
            await openai_ws.close()
        except:
            pass
        print("🔌 Connexions fermées")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
