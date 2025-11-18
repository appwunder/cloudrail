from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID


class ArchitectureNodeBase(BaseModel):
    """Base schema for architecture node"""
    id: str
    type: str
    position: dict
    data: dict
    style: Optional[dict] = None


class ArchitectureEdgeBase(BaseModel):
    """Base schema for architecture edge/connection"""
    id: str
    source: str
    target: str
    type: Optional[str] = None


class ArchitectureCreate(BaseModel):
    """Schema for creating architecture"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[dict] = Field(default_factory=list)
    edges: List[dict] = Field(default_factory=list)
    estimated_monthly_cost: Optional[str] = None
    is_public: bool = False


class ArchitectureUpdate(BaseModel):
    """Schema for updating architecture"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[dict]] = None
    edges: Optional[List[dict]] = None
    estimated_monthly_cost: Optional[str] = None
    is_public: Optional[bool] = None


class ArchitectureResponse(BaseModel):
    """Schema for architecture response"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    nodes: List[dict]
    edges: List[dict]
    estimated_monthly_cost: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArchitectureListResponse(BaseModel):
    """Schema for list of architectures"""
    architectures: List[ArchitectureResponse]
    total: int
