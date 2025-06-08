import os
from fastapi import FastAPI, Request, Response

# Variables d'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL")

print(f"🚀 RAILWAY_URL = {RAILWAY_URL}")
print(f"🚀 OPENAI_API_KEY present? {'yes' if OPENAI_API_KEY else 'no'}")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Serveur Twilio + OpenAI actif!", "railway_url": RAILWAY_URL}

@app.post("/incoming-call")
async def incoming_call(request: Request):
    """
    Endpoint appelé par Twilio quand quelqu'un appelle votre numéro.
    Pour l'instant, on fait juste un message vocal de test.
    """
    print("📞 Appel reçu!")
    
    # Pour débugger, on peut voir les données envoyées par Twilio
    form_data = await request.form()
    print(f"📋 Données Twilio: {dict(form_data)}")
    
    # TwiML simple pour test
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="fr-FR">
            Bonjour ! Votre intégration Twilio avec Railway fonctionne parfaitement. 
            Vous entendez ce message depuis votre serveur FastAPI déployé sur Railway.
        </Say>
        <Pause length="2"/>
        <Say voice="alice" language="fr-FR">
            Prochaine étape : intégrer OpenAI pour des conversations intelligentes !
        </Say>
        <Pause length="1"/> 
        <Hangup/>
    </Response>"""
    
    print("✅ TwiML envoyé à Twilio")
    return Response(content=twiml, media_type="application/xml")

# Endpoint de test pour vérifier que le serveur fonctionne
@app.get("/test")
async def test():
    return {
        "status": "OK", 
        "message": "Serveur en marche",
        "railway_url": RAILWAY_URL,
        "openai_configured": bool(OPENAI_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
