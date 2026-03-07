from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

from datetime import datetime, timedelta, timezone
from sqlalchemy import func

from typing import Optional
from decimal import Decimal

import services

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

    try:
        return services.create_tool(db, tool)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tools/{tool_id}",response_model=schemas.ToolDetailResponse, tags=["Outils"])
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """Récupère les détails d'un outil"""

    tool_detail = services.get_tool_detail(db, tool_id)
    if not tool_detail:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool_detail

@app.put("/api/tools/{tool_id}",response_model=schemas.ToolResponse, tags=["Outils"])
def update_tool(tool_id: int, tool_update: schemas.ToolUpdate, db: Session = Depends(get_db)):
    """Modifie les information d'un outil"""

    try:
        updated_tool = services.update_tool(db, tool_id, tool_update)
        if not updated_tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return updated_tool
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tools", response_model=schemas.PaginatedToolResponse, tags=["Outils"])
def list_tools(
    skip: int = 0, 
    limit: int = 10, 
    name: Optional[str] = None,
    vendor: Optional[str] = None,
    category: Optional[str] = None, 
    department: Optional[models.DepartmentType] = None, 
    status: Optional[models.ToolStatusType] = None, 
    monthly_cost_min: Optional[Decimal] = None,
    monthly_cost_max: Optional[Decimal] = None,
    active_users_count_min: Optional[int] = None,
    active_users_count_max: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Liste les outils avec système de pagination et filtres dynamiques."""
    
    return services.list_tools(
        db, skip, limit, name, vendor, category, department, status,
        monthly_cost_min, monthly_cost_max, active_users_count_min, active_users_count_max
    )