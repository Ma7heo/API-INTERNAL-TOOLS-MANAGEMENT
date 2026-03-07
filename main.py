from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

from datetime import datetime, timedelta, timezone
from sqlalchemy import func

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

@app.get("/api/tools/{tool_id}",response_model=schemas.ToolDetailResponse, tags=["Outils"])
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """Récupère les détails d'un outil"""

    tool = db.query(models.Tool).filter(models.Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    total_monthly_cost = tool.monthly_cost * tool.active_users_count

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    usage_stats = db.query(
        func.count(models.UsageLog.id).label("total_sessions"),
        func.avg(models.UsageLog.usage_minutes).label("avg_minutes")
    ).filter(
        models.UsageLog.tool_id == tool_id,
        models.UsageLog.session_date >= thirty_days_ago.date()
    ).first()

    total_sessions = usage_stats.total_sessions or 0
    avg_session_minutes = int(usage_stats.avg_minutes) if usage_stats.avg_minutes else 0
    
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "vendor": tool.vendor,
        "website_url": str(tool.website_url) if tool.website_url else None,
        "monthly_cost": tool.monthly_cost,
        "owner_department": tool.owner_department,
        "category": tool.category.name,
        "status": tool.status,
        "active_users_count": tool.active_users_count,
        "created_at": tool.created_at,
        "updated_at": tool.updated_at,
        "total_monthly_cost": total_monthly_cost,
        "usage_metrics": {
            "last_30_days": {
                "total_sessions": total_sessions,
                "avg_session_minutes": avg_session_minutes
            }
        }

    }