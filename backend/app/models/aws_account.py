from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class AWSAccount(Base):
    """AWS Account linked to a tenant"""
    __tablename__ = "aws_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    account_id = Column(String, nullable=False)
    account_name = Column(String)
    role_arn = Column(String, nullable=False)  # IAM role ARN for cross-account access
    external_id = Column(String)  # For additional security
    region = Column(String, default="us-east-1")
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(String, default="pending")  # pending, syncing, success, error
    config_data = Column(JSON)  # Additional configuration (renamed from metadata to avoid SQLAlchemy conflict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="aws_accounts")
    budgets = relationship("Budget", back_populates="account")
