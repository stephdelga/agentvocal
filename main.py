import os
from openai import OpenAI
from fastapi import FastAPI, Response, Form

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL", "agentvocal-production.up.railway.app")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Assistant vocal intelligent actif"}

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
    
    # Pendant que Twilio transcrit, on dit qu'on traite
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
    """Reçoit la transcription et génère une réponse avec OpenAI"""
    print(f"📝 Transcription: {TranscriptionText}")
    
    try:
        # Appel à OpenAI pour générer une réponse intelligente
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """Tu es un assistant vocal français professionnel et amical.
                    Tu aides les clients avec leurs questions.
                    Réponds de manière claire, concise et utile.
                    Si on te demande des tarifs, dis que tu vas chercher les informations."""
                },
                {
                    "role": "user", 
                    "content": TranscriptionText
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        print(f"🤖 Réponse IA: {ai_response}")
        
        # Stocker la réponse pour le prochain appel
        # (Dans une vraie app, utiliser une base de données)
        # Pour l'instant, on log juste
        
        return {"status": "success", "response": ai_response, "call_sid": CallSid}
        
    except Exception as e:
        print(f"❌ Erreur OpenAI: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/wait-for-response")
def wait_for_response():
    """Endpoint temporaire en attendant une vraie gestion des réponses"""
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Merci pour votre question ! 
        Votre demande a été traitée par intelligence artificielle.
        Bientôt, je pourrai vous répondre directement par téléphone !
    </Say>
    <Pause length="1"/>
    <Say voice="alice" language="fr-FR">
        Au revoir !
    </Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

# Endpoint pour tester OpenAI
@app.post("/test-ai")
def test_ai(question: str = Form(...)):
    """Test de l'IA via formulaire"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant français utile."},
                {"role": "user", "content": question}
            ],
            max_tokens=100
        )
        return {"question": question, "response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
