import os
import sys
from fastapi import FastAPI, Response, Form

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAILWAY_URL = os.getenv("RAILWAY_URL", "agentvocal-production.up.railway.app")

print(f"🔑 OpenAI Key présente: {'Oui' if OPENAI_API_KEY else 'Non'}")
print(f"🔑 OpenAI Key length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")
print(f"🐍 Python version: {sys.version}")

# Test d'import OpenAI avec diagnostics détaillés
openai_client = None
openai_error = None

try:
    print("📦 Tentative d'import OpenAI...")
    from openai import OpenAI
    print("✅ Import OpenAI réussi")
    
    if OPENAI_API_KEY:
        print("🔧 Création du client OpenAI...")
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ Client OpenAI créé avec succès")
    else:
        print("❌ Pas de clé API OpenAI")
        
except ImportError as e:
    openai_error = f"Import Error: {e}"
    print(f"❌ Erreur d'import OpenAI: {e}")
except Exception as e:
    openai_error = f"Autre erreur: {e}"
    print(f"❌ Erreur création client OpenAI: {e}")

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "OK", 
        "message": "Assistant vocal intelligent actif",
        "openai_configured": bool(openai_client),
        "openai_key_present": bool(OPENAI_API_KEY),
        "openai_key_length": len(OPENAI_API_KEY) if OPENAI_API_KEY else 0,
        "openai_error": openai_error,
        "python_version": sys.version
    }

@app.get("/debug")
def debug():
    """Endpoint de debug détaillé"""
    try:
        # Test des imports
        import_results = {}
        
        try:
            import openai
            import_results["openai"] = "✅ OK"
        except Exception as e:
            import_results["openai"] = f"❌ {e}"
            
        try:
            from openai import OpenAI
            import_results["openai.OpenAI"] = "✅ OK"
        except Exception as e:
            import_results["openai.OpenAI"] = f"❌ {e}"
        
        return {
            "imports": import_results,
            "env_vars": {
                "OPENAI_API_KEY": "Present" if OPENAI_API_KEY else "Missing",
                "RAILWAY_URL": RAILWAY_URL
            },
            "python_path": sys.path[:3]  # Premier 3 chemins
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/incoming-call")
def incoming_call():
    """Point d'entrée pour les appels Twilio"""
    print("📞 Appel reçu")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="fr-FR">
        Bonjour ! Version diagnostic active. Test en cours.
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
        "openai_available": bool(openai_client)
    }
