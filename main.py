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

@app.put("/api/tools/{tool_id}",response_model=schemas.ToolResponse, tags=["Outils"])
def update_tool(tool_id: int, tool_update: schemas.ToolUpdate, db: Session = Depends(get_db)):
    """Modifie les information d'un outil"""

    db_tool = db.query(models.Tool).filter(models.Tool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if tool_update.category_id is not None:
        category = db.query(models.Category).filter(models.Category.id == tool_update.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category ID does not exist")
    
    if tool_update.name is not None and tool_update.name != db_tool.name:
        existing_tool = db.query(models.Tool).filter(models.Tool.name == tool_update.name).first()
        if existing_tool:
            raise HTTPException(status_code=400, detail="Tool name already exists")
    
    update_data = tool_update.model_dump(exclude_unset=True)
    
    if "website_url" in update_data and update_data["website_url"] is not None:
        update_data["website_url"] = str(update_data["website_url"])

    for key, value in update_data.items():
        setattr(db_tool, key, value)
    
    db.commit()
    db.refresh(db_tool)

    return db_tool


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
    
    query = db.query(models.Tool)
    total_tools = query.count()
    filters_applied = {}
    
    if name:
        query = query.filter(models.Tool.name.ilike(f"%{name}%"))
        filters_applied["name"] = name
        
    if vendor:
        query = query.filter(models.Tool.vendor.ilike(f"%{vendor}%"))
        filters_applied["vendor"] = vendor
        
    if category:
        query = query.join(models.Category).filter(models.Category.name.ilike(f"%{category}%"))
        filters_applied["category"] = category
        
    if department:
        query = query.filter(models.Tool.owner_department == department)
        filters_applied["department"] = department.value
        
    if status:
        query = query.filter(models.Tool.status == status)
        filters_applied["status"] = status.value
        
    if monthly_cost_min is not None:
        query = query.filter(models.Tool.monthly_cost >= monthly_cost_min)
        filters_applied["monthly_cost_min"] = float(monthly_cost_min) 
        
    if monthly_cost_max is not None:
        query = query.filter(models.Tool.monthly_cost <= monthly_cost_max)
        filters_applied["monthly_cost_max"] = float(monthly_cost_max)
        
    if active_users_count_min is not None:
        query = query.filter(models.Tool.active_users_count >= active_users_count_min)
        filters_applied["active_users_count_min"] = active_users_count_min
        
    if active_users_count_max is not None:
        query = query.filter(models.Tool.active_users_count <= active_users_count_max)
        filters_applied["active_users_count_max"] = active_users_count_max
        
    filtered_tools_count = query.count()
    
    tools = query.offset(skip).limit(limit).all()
    
    return {
        "data": tools,
        "total": total_tools,
        "filtered": filtered_tools_count,
        "filters_applied": filters_applied
    }