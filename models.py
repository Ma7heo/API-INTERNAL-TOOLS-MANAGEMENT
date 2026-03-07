import enum
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

class DepartmentType(str, enum.Enum):
    Engineering = 'Engineering'
    Sales = 'Sales'
    Marketing = 'Marketing'
    HR = 'HR'
    Finance = 'Finance'
    Operations = 'Operations'
    Design = 'Design'

class ToolStatusType(str, enum.Enum):
    active = 'active'
    deprecated = 'deprecated'
    trial = 'trial'

class Category(Base):
    __tablename__ = "categories" 

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    color_hex = Column(String(7), default='#6366f1')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tools = relationship("Tool", back_populates="category")

class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    vendor = Column(String(100))
    website_url = Column(String(255))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    monthly_cost = Column(Numeric(10, 2), nullable=False)
    active_users_count = Column(Integer, default=0, nullable=False)
    
    owner_department = Column(Enum(DepartmentType), nullable=False)
    status = Column(Enum(ToolStatusType), default=ToolStatusType.active)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="tools")
    usage_logs = relationship("UsageLog", back_populates="tool", cascade="all, delete-orphan")

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    session_date = Column(Date, nullable=False)
    usage_minutes = Column(Integer, default=0)
    actions_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tool = relationship("Tool", back_populates="usage_logs")