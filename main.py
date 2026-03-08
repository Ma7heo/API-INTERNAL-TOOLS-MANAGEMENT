from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
import logging

import models
import schemas
from database import get_db
import services


app = FastAPI(
    title="Internal Toll API",
    description="API REST pour la gestion des outils SaaS internes de TechCorp Solutions.",
    version="1.0.0",
    docs_url="/api/docs"
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("TechCorp_API")

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
    logger.info(f"Tentative de création d'un nouvel outil : {tool.name} par le département {tool.owner_department}")
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
    logger.info(f"Tentative de mise à jour pour l'outil ID: {tool_id}")
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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Intercepte les crashs imprévus (500) pour ne pas fuiter le code interne."""
    logger.error(f"Erreur critique sur la route {request.url.path} : {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal Server Error - Quelque chose s'est mal passé côté serveur."
            }
        }
    )


@app.get("/api/analytics/department-costs", response_model=schemas.DepartmentCostResponse, tags=["Analytics"])
def get_department_costs_analytics(
    sort_by: str = Query("total_cost", description="Champ sur lequel trier les résultats"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Ordre de tri (asc ou desc)"),
    db: Session = Depends(get_db)
):
    """Analyse la répartition des coûts des outils par département (Stakeholder: CFO)."""
    return services.get_department_costs(db, sort_by, order)

@app.get("/api/analytics/expensive-tools", tags=["Analytics"])
def get_expensive_tools_analytics(
    limit: int = Query(10, description="Nombre max d'outils à retourner"),
    min_cost: Optional[float] = Query(None, description="Filtre : Coût mensuel minimum"),
    db: Session = Depends(get_db)
):
    """Identifie les outils les plus coûteux et calcule les économies potentielles (Stakeholder: CFO)."""
    
    errors = {}
    
    if limit < 1:
        errors["limit"] = "Must be positive integer"
        
    if min_cost is not None and min_cost < 0:
        errors["min_cost"] = "Must be a positive number"

    if errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Invalid analytics parameter",
                "details": errors
            }
        )
    
    response_data = services.get_expensive_tools(db, limit, min_cost)
    return schemas.ExpensiveToolsResponse(**response_data)