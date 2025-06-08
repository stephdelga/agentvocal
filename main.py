import os
from fastapi import FastAPI, Response, Form

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL", "agentvocal-production.up.railway.app")

print(f"🔑 OpenAI Key présente: {'Oui' if OPENAI_API_KEY else 'Non'}")

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "OK", 
        "message": "Assistant vocal intelligent actif",
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.post("/incoming-call")
def incoming_call():
    """Point d'entrée pour les appels Twilio"""
    print("📞 Appel reçu - démarrage conversation intelligente")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Bonjour ! Je suis votre assistant vocal intelligent. 
        Posez-moi une question après le bip, je vous répondrai.
    </Say>
    <Record 
        action="https://{RAILWAY_URL}/process-voice"
        method="POST"
        maxLength="30"
        timeout="5"
        finishOnKey="#"
        transcribe="true"
        transcribeCallback="https://{RAILWAY_URL}/handle-response"
    />
    <Say voice="alice" language="fr-FR">
        Je n'ai pas entendu votre question. Au revoir !
    </Say>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/process-voice")
def process_voice(RecordingUrl: str = Form(...), CallSid: str = Form(...)):
    """Traite l'enregistrement vocal de l'utilisateur"""
    print(f"🎵 Enregistrement reçu: {RecordingUrl}")
    print(f"📞 Call ID: {CallSid}")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Un moment, je traite votre demande...
    </Say>
    <Pause length="3"/>
    <Say voice="alice" language="fr-FR">
        Je vous prépare une réponse intelligente.
    </Say>
    <Pause length="2"/>
    <Redirect>/wait-for-response</Redirect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/handle-response")
def handle_response(
    TranscriptionText: str = Form(...), 
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...)
):
    """Reçoit la transcription et génère une réponse"""
    print(f"📝 Transcription: {TranscriptionText}")
    
    # Réponse simple sans OpenAI pour l'instant
    simple_response = f"J'ai bien entendu: {TranscriptionText}. Merci pour votre message!"
    
    print(f"💬 Réponse simple: {simple_response}")
    
    return {"status": "success", "response": simple_response, "call_sid": CallSid}

@app.get("/wait-for-response")
def wait_for_response():
    """Endpoint temporaire"""
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Merci pour votre question ! 
        Votre demande a été reçue et traitée.
        L'intelligence artificielle sera bientôt intégrée !
    </Say>
    <Pause length="1"/>
    <Say voice="alice" language="fr-FR">
        Au revoir !
    </Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/test-simple")
def test_simple(question: str = Form(...)):
    """Test simple sans OpenAI"""
    return {
        "question": question, 
        "response": f"Test reçu: {question}",
        "openai_key_present": bool(OPENAI_API_KEY)
    }
