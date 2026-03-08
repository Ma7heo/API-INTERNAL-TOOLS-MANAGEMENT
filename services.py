from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import models
import schemas

def create_tool(db: Session, tool: schemas.ToolCreate):
    category = db.query(models.Category).filter(models.Category.id == tool.category_id).first()
    if not category:
        raise ValueError("Category ID does not exist")
    
    existing_tool = db.query(models.Tool).filter(models.Tool.name == tool.name).first()
    if existing_tool:
        raise ValueError("Tool name already exists")
    
    tool_data = tool.model_dump()
    if tool_data.get("website_url"):
        tool_data["website_url"] = str(tool_data["website_url"])
    
    new_tool = models.Tool(**tool_data)
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    return new_tool

def get_tool_detail(db: Session, tool_id: int):
    tool = db.query(models.Tool).filter(models.Tool.id == tool_id).first()
    if not tool:
        return None

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

def update_tool(db: Session, tool_id: int, tool_update: schemas.ToolUpdate):
    db_tool = db.query(models.Tool).filter(models.Tool.id == tool_id).first()
    if not db_tool:
        return None
    
    if tool_update.category_id is not None:
        category = db.query(models.Category).filter(models.Category.id == tool_update.category_id).first()
        if not category:
            raise ValueError("Category ID does not exist")
            
    if tool_update.name is not None and tool_update.name != db_tool.name:
        existing_tool = db.query(models.Tool).filter(models.Tool.name == tool_update.name).first()
        if existing_tool:
            raise ValueError("Tool name already exists")

    update_data = tool_update.model_dump(exclude_unset=True)
    if "website_url" in update_data and update_data["website_url"] is not None:
        update_data["website_url"] = str(update_data["website_url"])
        
    for key, value in update_data.items():
        setattr(db_tool, key, value)
        
    db.commit()
    db.refresh(db_tool)
    return db_tool

def list_tools(
    db: Session,
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
    active_users_count_max: Optional[int] = None
):
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

def get_department_costs(db: Session, sort_by: str = "total_cost", order: str = "desc"):
    
    total_company_cost_query = db.query(func.sum(models.Tool.monthly_cost)).filter(models.Tool.status == "active").scalar()
    total_company_cost = float(total_company_cost_query) if total_company_cost_query else 0.0

    if total_company_cost == 0:
        return {
            "data": [],
            "summary": {"total_company_cost": 0.0, "departments_count": 0, "most_expensive_department": None},
            "message": "No analytics data available - ensure tools data exists"
        }
    
    dept_stats = db.query(
        models.Tool.owner_department.label("department"),
        func.sum(models.Tool.monthly_cost).label("total_cost"),
        func.count(models.Tool.id).label("tools_count"),
        func.sum(models.Tool.active_users_count).label("total_users")
    ).filter(
        models.Tool.status == "active"
    ).group_by(
        models.Tool.owner_department
    ).all()

    data_list = []
    for stat in dept_stats:
        dept_name = stat.department.value if hasattr(stat.department, 'value') else stat.department
        
        total_cost = float(stat.total_cost or 0)
        tools_count = int(stat.tools_count or 0)
        total_users = int(stat.total_users or 0)
        
        avg_cost = round(total_cost / tools_count, 2) if tools_count > 0 else 0.0
        percentage = round((total_cost / total_company_cost) * 100, 1)

        data_list.append({
            "department": dept_name,
            "total_cost": round(total_cost, 2),
            "tools_count": tools_count,
            "total_users": total_users,
            "average_cost_per_tool": avg_cost,
            "cost_percentage": percentage
        })
    
    valid_sort_keys = ["department", "total_cost", "tools_count", "total_users", "average_cost_per_tool", "cost_percentage"]
    if sort_by not in valid_sort_keys:
        sort_by = "total_cost"
    
    reverse_sort = order.lower() == "desc"
    data_list.sort(key=lambda x: x[sort_by], reverse=reverse_sort)

    sorted_for_most_expensive = sorted(data_list, key=lambda x: (-x["total_cost"], x["department"]))
    most_expensive_dept = sorted_for_most_expensive[0]["department"] if sorted_for_most_expensive else None

    return {
        "data": data_list,
        "summary": {
            "total_company_cost": round(total_company_cost, 2),
            "departments_count": len(data_list),
            "most_expensive_department": most_expensive_dept
        }
    }