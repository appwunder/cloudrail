from pydantic import BaseModel
from datetime import datetime
import uuid


class TenantBase(BaseModel):
    name: str
    slug: str


class TenantCreate(BaseModel):
    name: str


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
