import os
from fastapi import FastAPI, Response, Form

RAILWAY_URL = os.getenv("RAILWAY_URL")
app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Serveur avec reconnaissance vocale"}

@app.post("/incoming-call")
def incoming_call():
    """Utilise <Record> et <Gather> pour capturer la voix"""
    print("📞 Appel reçu - mode reconnaissance vocale")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Bonjour ! Je suis votre assistant intelligent. 
        Parlez après le bip, je vous écouterai.
    </Say>
    <Record 
        action="https://{RAILWAY_URL}/process-recording"
        method="POST"
        maxLength="30"
        finishOnKey="#"
        transcribe="true"
        transcribeCallback="https://{RAILWAY_URL}/process-transcription"
    />
    <Say voice="alice" language="fr-FR">
        Je n'ai pas entendu votre message. Au revoir !
    </Say>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/process-recording")
def process_recording(RecordingUrl: str = Form(...), CallSid: str = Form(...)):
    """Appelé quand l'enregistrement est terminé"""
    print(f"🎵 Enregistrement reçu: {RecordingUrl}")
    
    # Pour l'instant, on dit juste qu'on a reçu
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Merci ! J'ai bien reçu votre message. 
        Je le traite avec intelligence artificielle.
    </Say>
    <Pause length="2"/>
    <Say voice="alice" language="fr-FR">
        Bientôt, je pourrai vous répondre intelligemment en temps réel !
    </Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/process-transcription")
def process_transcription(
    TranscriptionText: str = Form(...), 
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...)
):
    """Appelé quand la transcription est prête"""
    print(f"📝 Transcription: {TranscriptionText}")
    
    # Ici on pourrait appeler OpenAI API avec le texte
    # et renvoyer une réponse intelligente
    
    return {"status": "received", "transcription": TranscriptionText}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
