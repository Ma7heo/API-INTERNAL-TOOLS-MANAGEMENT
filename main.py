from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

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

@app.post("/api/tools",response_model=schemas.ToolResponse, status_code=status.HTTP_201_CREATED, tags=["Outils"])
def create_tool(tool: schemas.ToolCreate, db: Session = Depends(get_db)):
    """Ajoute un nouvel outil au catalogue."""

    category = db.query(models.Category).filter(models.Category.id == tool.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category ID does not exist")
    
    existing_tool = db.query(models.Tool).filter(models.Tool.name == tool.name).first()
    if existing_tool:
        raise HTTPException(status_code=400, detail="Tool name already exists")
    
    tool_data = tool.model_dump()
    
    if tool_data.get("website_url"):
        tool_data["website_url"] = str(tool_data["website_url"])
    
    new_tool = models.Tool(**tool_data)

    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)

    return new_tool