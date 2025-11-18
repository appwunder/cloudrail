from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class CloudProvider(str, enum.Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ALIBABA = "alibaba"


class CloudAccount(Base):
    """Multi-cloud account linked to a tenant"""
    __tablename__ = "cloud_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Cloud Provider
    provider = Column(SQLEnum(CloudProvider), nullable=False)

    # Account Information
    account_id = Column(String, nullable=False)  # AWS Account ID, GCP Project ID, Azure Subscription ID, etc.
    account_name = Column(String)

    # Credentials (encrypted JSONB) - provider-specific
    # AWS: { "role_arn": "...", "external_id": "..." }
    # GCP: { "service_account_json": {...} }
    # Azure: { "tenant_id": "...", "client_id": "...", "client_secret": "..." }
    # Alibaba: { "access_key_id": "...", "access_key_secret": "..." }
    credentials = Column(JSON, nullable=False)

    # Regional and Currency Settings
    region = Column(String)  # Default region for this account
    currency = Column(String, default="USD")  # USD, EUR, GBP, CNY, etc.

    # Sync Status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(String, default="pending")  # pending, syncing, success, error
    sync_error = Column(String)  # Last sync error message if any

    # Additional Configuration
    config_data = Column(JSON)  # Provider-specific configuration

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="cloud_accounts")
