from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.budget import BudgetPeriod, NotificationChannel


class BudgetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    budget_amount: float = Field(..., gt=0, description="Budget amount in USD")
    period: BudgetPeriod = Field(default=BudgetPeriod.MONTHLY, description="Budget period")

    # Optional filters
    account_id: Optional[UUID] = Field(None, description="AWS Account ID (null for tenant-wide)")
    service_name: Optional[str] = Field(None, description="AWS service name filter")
    region: Optional[str] = Field(None, description="AWS region filter")

    # Alerting configuration
    threshold_percentage: int = Field(default=80, ge=1, le=100, description="Alert threshold percentage")
    notification_channels: List[str] = Field(default=["email"], description="Notification channels")
    notification_emails: Optional[List[str]] = Field(None, description="Email addresses for notifications")
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook URL")
    custom_webhook_url: Optional[str] = Field(None, description="Custom webhook URL")

    is_active: bool = Field(default=True, description="Whether budget is active")

    @validator('notification_channels', each_item=True)
    def validate_notification_channel(cls, v):
        valid_channels = [c.value for c in NotificationChannel]
        if v not in valid_channels:
            raise ValueError(f"Invalid notification channel. Must be one of: {valid_channels}")
        return v

    @validator('notification_emails')
    def validate_emails(cls, v, values):
        if v and 'email' in values.get('notification_channels', []):
            if not v:
                raise ValueError("notification_emails required when email channel is enabled")
        return v


class BudgetCreate(BudgetBase):
    """Schema for creating a new budget"""
    pass


class BudgetUpdate(BaseModel):
    """Schema for updating an existing budget"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    budget_amount: Optional[float] = Field(None, gt=0)
    period: Optional[BudgetPeriod] = None
    account_id: Optional[UUID] = None
    service_name: Optional[str] = None
    region: Optional[str] = None
    threshold_percentage: Optional[int] = Field(None, ge=1, le=100)
    notification_channels: Optional[List[str]] = None
    notification_emails: Optional[List[str]] = None
    slack_webhook_url: Optional[str] = None
    custom_webhook_url: Optional[str] = None
    is_active: Optional[bool] = None


class BudgetResponse(BudgetBase):
    """Schema for budget response"""
    id: UUID
    tenant_id: UUID
    last_alert_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Current status
    current_spend: Optional[float] = Field(None, description="Current spending in period")
    percentage_used: Optional[float] = Field(None, description="Percentage of budget used")
    days_remaining: Optional[int] = Field(None, description="Days remaining in period")
    is_over_budget: Optional[bool] = Field(None, description="Whether budget is exceeded")
    is_over_threshold: Optional[bool] = Field(None, description="Whether threshold is exceeded")

    class Config:
        from_attributes = True


class BudgetListResponse(BaseModel):
    """Schema for paginated budget list"""
    budgets: List[BudgetResponse]
    total: int
    page: int
    page_size: int


class BudgetAlertResponse(BaseModel):
    """Schema for budget alert response"""
    id: UUID
    budget_id: UUID
    alert_type: str
    current_amount: float
    budget_amount: float
    percentage_used: float
    period_start: datetime
    period_end: datetime
    notification_sent: bool
    notification_sent_at: Optional[datetime]
    notification_channels_used: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    """Schema for budget status check"""
    budget_id: UUID
    budget_name: str
    budget_amount: float
    current_spend: float
    percentage_used: float
    threshold_percentage: int
    is_over_threshold: bool
    is_over_budget: bool
    days_into_period: int
    days_remaining: int
    projected_spend: Optional[float] = None
    will_exceed_budget: Optional[bool] = None
