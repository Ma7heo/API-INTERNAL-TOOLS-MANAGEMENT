from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Internal Toll API",
    description="API REST pour la gestion des outils SaaS internes de TechCorp Solutions.",
    version="1.0.0",
    docs_url="/api/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/", tags=["Système"])
def health_check():
    """Verify the good connection of the API"""
    return{
        "status": "online",
        "message": "Bienvenue sur l'API Internal Tools Management. Visitez /api/docs pour la documentation."
    }