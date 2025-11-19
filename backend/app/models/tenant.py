from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class Tenant(Base):
    """Multi-tenant model - each tenant represents an organization/customer"""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Stripe / Subscription
    stripe_customer_id = Column(String, unique=True, nullable=True)
    subscription_status = Column(String, default="free")  # free, active, past_due, canceled
    subscription_plan = Column(String, default="free")    # free, pro, business, enterprise

    # Relationships
    users = relationship("User", back_populates="tenant")
    aws_accounts = relationship("AWSAccount", back_populates="tenant")
    cloud_accounts = relationship("CloudAccount", back_populates="tenant")
    architectures = relationship("Architecture", back_populates="tenant")
    budgets = relationship("Budget", back_populates="tenant")
