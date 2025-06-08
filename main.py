from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK"}

@app.post("/incoming-call")
def incoming_call():
    print("📞 Appel reçu")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">Bonjour, test simple qui marche</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")
