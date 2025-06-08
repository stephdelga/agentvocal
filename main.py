import os
from openai import OpenAI
from fastapi import FastAPI, Response, Form

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL", "agentvocal-production.up.railway.app")

client = OpenAI(api_key=OPENAI_API_KEY)
print("✅ Assistant vocal intelligent avec OpenAI prêt !")

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Assistant vocal intelligent avec IA active"}

@app.post("/incoming-call")
def incoming_call():
    """Point d'entrée pour les appels Twilio"""
    print("📞 Appel reçu - conversation IA")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Bonjour ! Je suis votre assistant vocal intelligent. 
        Posez-moi une question après le bip, je vous répondrai avec intelligence artificielle.
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
    """Traite l'enregistrement vocal"""
    print(f"🎵 Enregistrement reçu: {RecordingUrl}")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Parfait ! Je traite votre question avec intelligence artificielle...
    </Say>
    <Pause length="4"/>
    <Redirect>/give-ai-response</Redirect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

# Variable globale pour stocker la dernière réponse IA (temporaire)
last_ai_response = "Désolé, je n'ai pas pu traiter votre demande."

@app.post("/handle-response")
def handle_response(
    TranscriptionText: str = Form(...), 
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...)
):
    """Reçoit la transcription et génère une réponse IA"""
    global last_ai_response
    
    print(f"📝 Transcription: {TranscriptionText}")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """Tu es un assistant vocal français professionnel et amical.
                    Tu aides les clients avec leurs questions.
                    Réponds de manière claire et concise en 2-3 phrases maximum.
                    Tu peux aider avec des informations générales, des conseils, etc.
                    Si on te demande des tarifs spécifiques, dis que tu vas chercher les informations."""
                },
                {
                    "role": "user", 
                    "content": TranscriptionText
                }
            ],
            max_tokens=120,
            temperature=0.7
        )
        
        last_ai_response = response.choices[0].message.content
        print(f"🤖 Réponse IA générée: {last_ai_response}")
        
        return {"status": "success", "response": last_ai_response}
        
    except Exception as e:
        print(f"❌ Erreur OpenAI: {e}")
        last_ai_response = "Désolé, j'ai eu un problème technique. Pouvez-vous répéter votre question ?"
        return {"status": "error", "error": str(e)}

@app.get("/give-ai-response")
def give_ai_response():
    """Donne la réponse IA vocalement"""
    global last_ai_response
    
    print(f"🎙️ Réponse vocale: {last_ai_response}")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">{last_ai_response}</Say>
    <Pause length="1"/>
    <Say voice="alice" language="fr-FR">
        Avez-vous d'autres questions ? Sinon, au revoir !
    </Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/test-ai")
def test_ai(question: str = Form(...)):
    """Test direct de l'IA"""
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
