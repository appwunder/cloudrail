from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.cloud_account import CloudProvider


class CloudAccountCreate(BaseModel):
    """Schema for creating a cloud account"""
    provider: CloudProvider
    account_id: str = Field(..., min_length=1, max_length=255, description="Cloud account/project/subscription ID")
    account_name: Optional[str] = Field(None, max_length=255, description="Friendly name for this account")
    credentials: Dict[str, Any] = Field(..., description="Provider-specific credentials (encrypted)")
    region: Optional[str] = Field(None, description="Default region for this account")
    currency: str = Field(default="USD", description="Preferred currency (USD, EUR, GBP, CNY, etc.)")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Additional provider-specific configuration")

    @validator('credentials')
    def validate_credentials(cls, v, values):
        """Validate credentials based on provider"""
        if 'provider' not in values:
            return v

        provider = values['provider']

        # AWS credentials validation
        if provider == CloudProvider.AWS:
            required_fields = ['role_arn']
            if not all(field in v for field in required_fields):
                raise ValueError(f"AWS credentials must include: {required_fields}")

        # GCP credentials validation
        elif provider == CloudProvider.GCP:
            required_fields = ['service_account_json']
            if not all(field in v for field in required_fields):
                raise ValueError(f"GCP credentials must include: {required_fields}")

        # Azure credentials validation
        elif provider == CloudProvider.AZURE:
            required_fields = ['tenant_id', 'client_id', 'client_secret']
            if not all(field in v for field in required_fields):
                raise ValueError(f"Azure credentials must include: {required_fields}")

        # Alibaba credentials validation
        elif provider == CloudProvider.ALIBABA:
            required_fields = ['access_key_id', 'access_key_secret']
            if not all(field in v for field in required_fields):
                raise ValueError(f"Alibaba Cloud credentials must include: {required_fields}")

        return v


class CloudAccountUpdate(BaseModel):
    """Schema for updating a cloud account"""
    account_name: Optional[str] = Field(None, max_length=255)
    credentials: Optional[Dict[str, Any]] = None
    region: Optional[str] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    config_data: Optional[Dict[str, Any]] = None


class CloudAccountResponse(BaseModel):
    """Schema for cloud account response"""
    id: UUID
    tenant_id: UUID
    provider: CloudProvider
    account_id: str
    account_name: Optional[str] = None
    region: Optional[str] = None
    currency: str
    is_active: bool
    last_sync_at: Optional[datetime] = None
    sync_status: str
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Note: credentials are intentionally excluded from response for security

    class Config:
        from_attributes = True


class CloudAccountListResponse(BaseModel):
    """Schema for list of cloud accounts"""
    accounts: List[CloudAccountResponse]
    total: int


class CloudAccountSyncRequest(BaseModel):
    """Schema for triggering a sync"""
    force: bool = Field(default=False, description="Force sync even if recently synced")


class CloudAccountSyncResponse(BaseModel):
    """Schema for sync response"""
    account_id: UUID
    provider: CloudProvider
    sync_status: str
    message: str
    last_sync_at: Optional[datetime] = None
