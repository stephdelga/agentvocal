import os
from openai import OpenAI
from fastapi import FastAPI, Response, Form

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL", "agentvocal-production.up.railway.app")

client = OpenAI(api_key=OPENAI_API_KEY)
print("✅ Assistant vocal naturel avec OpenAI prêt !")

app = FastAPI()

# Variable globale pour stocker les réponses IA
conversation_responses = {}

@app.get("/")
def root():
    return {"status": "OK", "message": "Assistant vocal naturel actif"}

@app.post("/incoming-call")
def incoming_call():
    """Point d'entrée pour les appels Twilio"""
    print("📞 Appel reçu - conversation naturelle")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Bonjour ! Comment puis-je vous aider aujourd'hui ?
    </Say>
    <Record 
        action="https://{RAILWAY_URL}/process-voice"
        method="POST"
        maxLength="20"
        timeout="3"
        finishOnKey="#"
        transcribe="true"
        transcribeCallback="https://{RAILWAY_URL}/handle-response"
        playBeep="false"
    />
    <Say voice="alice" language="fr-FR">
        Je n'ai pas bien entendu. N'hésitez pas à me rappeler !
    </Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/process-voice")
def process_voice(RecordingUrl: str = Form(...), CallSid: str = Form(...)):
    """Traite l'enregistrement vocal"""
    print(f"🎵 Enregistrement reçu: {RecordingUrl} pour l'appel {CallSid}")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Un instant, je réfléchis à votre question...
    </Say>
    <Pause length="3"/>
    <Redirect>/give-ai-response</Redirect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/handle-response")
def handle_response(
    TranscriptionText: str = Form(...), 
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...)
):
    """Reçoit la transcription et génère une réponse IA naturelle"""
    global conversation_responses
    
    print(f"📝 Transcription reçue: '{TranscriptionText}' pour l'appel {CallSid}")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """Tu es un assistant téléphonique français très naturel et chaleureux.
                    Tu parles comme une vraie personne au téléphone, pas comme un robot.
                    Utilise un ton conversationnel et amical.
                    Réponds de manière concise (2-3 phrases max) car c'est au téléphone.
                    Évite les mots techniques ou robotiques.
                    Si la question n'est pas claire, demande poliment de préciser.
                    Tu peux aider avec des informations générales, des conseils pratiques.
                    Pour des tarifs spécifiques, propose de chercher ou de rappeler."""
                },
                {
                    "role": "user", 
                    "content": TranscriptionText
                }
            ],
            max_tokens=80,
            temperature=0.8
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Nettoyer la réponse pour qu'elle soit plus naturelle
        ai_response = ai_response.replace("assistant", "")
        ai_response = ai_response.replace("intelligence artificielle", "")
        ai_response = ai_response.replace("IA", "")
        
        # Stocker la réponse pour cet appel
        conversation_responses[CallSid] = ai_response
        
        print(f"🤖 Réponse IA pour {CallSid}: {ai_response}")
        
        return {"status": "success", "response": ai_response, "call_sid": CallSid}
        
    except Exception as e:
        print(f"❌ Erreur OpenAI pour {CallSid}: {e}")
        fallback = "Je n'ai pas bien compris votre question. Pouvez-vous reformuler ?"
        conversation_responses[CallSid] = fallback
        return {"status": "error", "response": fallback, "error": str(e)}

@app.get("/give-ai-response")
def give_ai_response(CallSid: str = None):
    """Donne la réponse IA vocalement de façon naturelle"""
    global conversation_responses
    
    # Récupérer la réponse pour cet appel
    ai_response = "Désolé, je n'ai pas pu traiter votre demande."
    
    # Chercher la réponse la plus récente si pas de CallSid
    if CallSid and CallSid in conversation_responses:
        ai_response = conversation_responses[CallSid]
        # Nettoyer après usage
        del conversation_responses[CallSid]
    elif conversation_responses:
        # Prendre la dernière réponse
        last_call = list(conversation_responses.keys())[-1]
        ai_response = conversation_responses[last_call]
        del conversation_responses[last_call]
    
    print(f"🎙️ Réponse vocale: {ai_response}")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR" rate="0.9">{ai_response}</Say>
    <Pause length="1"/>
    <Say voice="alice" language="fr-FR" rate="0.9">
        Y a-t-il autre chose que je puisse faire pour vous ?
    </Say>
    <Record 
        action="https://{RAILWAY_URL}/process-followup"
        method="POST"
        maxLength="15"
        timeout="3"
        finishOnKey="#"
        transcribe="true"
        playBeep="false"
    />
    <Say voice="alice" language="fr-FR">
        Très bien ! Bonne journée et à bientôt !
    </Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/process-followup")
def process_followup(RecordingUrl: str = Form(...), CallSid: str = Form(...)):
    """Gère les questions de suivi"""
    print(f"🔄 Question de suivi reçue pour {CallSid}")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Parfait, je regarde ça tout de suite...
    </Say>
    <Pause length="2"/>
    <Redirect>/give-ai-response</Redirect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/test-ai")
def test_ai(question: str = Form(...)):
    """Test direct de l'IA"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant téléphonique français naturel et amical."},
                {"role": "user", "content": question}
            ],
            max_tokens=80,
            temperature=0.8
        )
        return {"question": question, "response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
