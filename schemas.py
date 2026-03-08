from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

from models import DepartmentType, ToolStatusType

class ToolBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nom de l'outil (2-100 caractères)")
    description: Optional[str] = None
    vendor: str = Field(..., max_length=100, description="Fournisseur (max 100 caractères)")
    website_url: Optional[HttpUrl] = Field(None, description="URL valide du site web")
    monthly_cost: Decimal = Field(..., ge=0, decimal_places=2, description="Coût mensuel (positif, max 2 décimales)", json_schema_extra={"example": 8.50})
    owner_department: DepartmentType

class ToolCreate(ToolBase):
    """POST /api/tools"""
    category_id: int = Field(..., description="ID de la catégorie existante")

class ToolUpdate(BaseModel):
    """PUT /api/tools/:id """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    vendor: Optional[str] = Field(None, max_length=100)
    website_url: Optional[HttpUrl] = None
    category_id: Optional[int] = None
    monthly_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    owner_department: Optional[DepartmentType] = None
    status: Optional[ToolStatusType] = None

class ToolResponse(ToolBase):
    """GET /api/tools"""
    id: int
    category: str 
    status: ToolStatusType
    active_users_count: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_validator('category', mode='before')
    @classmethod
    def extract_category_name(cls, v):
        if hasattr(v, 'name'):
            return v.name
        return v

class UsageMetrics(BaseModel):
    total_sessions: int
    avg_session_minutes: int

class UsageMetricsWrapper(BaseModel):
    last_30_days: UsageMetrics

class ToolDetailResponse(ToolResponse):
    """GET /api/tools/:id"""
    total_monthly_cost: Decimal
    usage_metrics: UsageMetricsWrapper
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedToolResponse(BaseModel):
    data: list[ToolResponse]
    total: int
    filtered: int
    filters_applied: Dict[str, Any]



class DepartmentCostItem(BaseModel):
    department: str
    total_cost: float
    tools_count: int
    total_users: int
    average_cost_per_tool: float
    cost_percentage: float

class DepartmentCostSummary(BaseModel):
    total_company_cost: float
    departments_count: int
    most_expensive_department: Optional[str] = None

class DepartmentCostResponse(BaseModel):
    data: List[DepartmentCostItem]
    summary: DepartmentCostSummary
    message: Optional[str] = None



class ExpensiveToolItem(BaseModel):
    id: int
    name: str
    monthly_cost: float
    active_users_count: int
    cost_per_user: float
    department: str
    vendor: str
    efficiency_rating: str

class ExpensiveToolsAnalysis(BaseModel):
    total_tools_analyzed: int
    avg_cost_per_user_company: float
    potential_savings_identified: float

class ExpensiveToolsResponse(BaseModel):
    data: List[ExpensiveToolItem]
    analysis: ExpensiveToolsAnalysis
    message: Optional[str] = None




class CategoryAnalyticsItem(BaseModel):
    category_name: str
    tools_count: int
    total_cost: float
    total_users: int
    percentage_of_budget: float
    average_cost_per_user: float

class CategoryAnalyticsInsights(BaseModel):
    most_expensive_category: Optional[str] = None
    most_efficient_category: Optional[str] = None

class CategoryAnalyticsResponse(BaseModel):
    data: List[CategoryAnalyticsItem]
    insights: CategoryAnalyticsInsights
    message: Optional[str] = None


class LowUsageToolItem(BaseModel):
    id: int
    name: str
    monthly_cost: float
    active_users_count: int
    cost_per_user: float
    department: str
    vendor: str
    warning_level: str
    potential_action: str

class LowUsageSavingsAnalysis(BaseModel):
    total_underutilized_tools: int
    potential_monthly_savings: float
    potential_annual_savings: float

class LowUsageResponse(BaseModel):
    data: List[LowUsageToolItem]
    savings_analysis: LowUsageSavingsAnalysis
    message: Optional[str] = None



class VendorSummaryItem(BaseModel):
    vendor: str
    tools_count: int
    total_monthly_cost: float
    total_users: int
    departments: str 
    average_cost_per_user: float
    vendor_efficiency: str

class VendorInsights(BaseModel):
    most_expensive_vendor: Optional[str] = None
    most_efficient_vendor: Optional[str] = None
    single_tool_vendors: int

class VendorSummaryResponse(BaseModel):
    data: List[VendorSummaryItem]
    vendor_insights: VendorInsights