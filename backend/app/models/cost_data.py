from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index, Date, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base
from app.models.cloud_account import CloudProvider


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


class MultiCloudCostData(Base):
    """Multi-cloud cost data for all cloud providers (AWS, GCP, Azure, Alibaba)"""
    __tablename__ = "multi_cloud_cost_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cloud_account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id"), nullable=False)

    # Cloud Provider
    provider = Column(SQLEnum(CloudProvider), nullable=False)

    # Time dimension
    date = Column(Date, nullable=False)

    # Cost dimensions
    service_name = Column(String, nullable=False)  # e.g., "Compute Engine", "Virtual Machines"
    service_category = Column(String)  # e.g., "Compute", "Storage"
    resource_id = Column(String)  # Provider-specific resource ID
    resource_name = Column(String)  # Resource name/tag
    region = Column(String)  # e.g., "us-east-1", "eastus", "us-central1"

    # Cost metrics
    cost = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    usage_quantity = Column(Float)  # Usage amount (e.g., GB-hours, instance-hours)
    usage_unit = Column(String)  # Usage unit (e.g., "GB", "hours")

    # Metadata
    tags = Column(JSONB)  # Resource tags as JSON
    provider_metadata = Column(JSONB)  # Provider-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    cloud_account = relationship("CloudAccount")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_mcc_tenant_date', 'tenant_id', 'date'),
        Index('idx_mcc_account_date', 'cloud_account_id', 'date'),
        Index('idx_mcc_provider', 'provider'),
        Index('idx_mcc_service', 'service_name'),
        Index('idx_mcc_date', 'date'),
        Index('idx_mcc_provider_date', 'provider', 'date'),
    )
