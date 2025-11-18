from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class CostData(Base):
    """Daily cost data for AWS services"""
    __tablename__ = "cost_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)

    # Time dimension
    date = Column(Date, nullable=False)

    # Cost dimensions
    service = Column(String, nullable=False)  # e.g., "Amazon EC2", "Amazon S3"
    region = Column(String)  # e.g., "us-east-1"
    usage_type = Column(String)  # e.g., "DataTransfer-Out-Bytes"
    tags = Column(JSONB)  # Resource tags as JSON object

    # Cost metrics
    cost = Column(Float, nullable=False)  # Unblended cost
    currency = Column(String, default="USD")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    aws_account = relationship("AWSAccount")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_cost_tenant_date', 'tenant_id', 'date'),
        Index('idx_cost_account_date', 'aws_account_id', 'date'),
        Index('idx_cost_service', 'service'),
        Index('idx_cost_date', 'date'),
    )


class CostSummary(Base):
    """Pre-aggregated cost summaries for faster queries"""
    __tablename__ = "cost_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)

    # Aggregation period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String, nullable=False)  # daily, weekly, monthly

    # Aggregated metrics
    total_cost = Column(Float, nullable=False)
    service = Column(String)  # NULL for account-level summaries
    currency = Column(String, default="USD")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    aws_account = relationship("AWSAccount")

    # Indexes
    __table_args__ = (
        Index('idx_summary_tenant_period', 'tenant_id', 'period_start', 'period_end'),
        Index('idx_summary_account_period', 'aws_account_id', 'period_start', 'period_end'),
    )
