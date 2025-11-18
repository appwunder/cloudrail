from sqlalchemy import Column, String, Float, Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.base import Base


class BudgetPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=True, index=True)

    # Budget details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    budget_amount = Column(Float, nullable=False)  # In USD
    period = Column(Enum(BudgetPeriod), nullable=False, default=BudgetPeriod.MONTHLY)

    # Filtering
    service_name = Column(String, nullable=True)  # Optional: budget for specific service
    region = Column(String, nullable=True)  # Optional: budget for specific region

    # Alerting
    threshold_percentage = Column(Integer, nullable=False, default=80)  # Alert at 80% of budget
    notification_channels = Column(JSONB, nullable=False, default=["email"])  # ["email", "slack", "webhook"]
    notification_emails = Column(JSONB, nullable=True)  # List of email addresses
    slack_webhook_url = Column(String, nullable=True)
    custom_webhook_url = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_alert_sent_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="budgets")
    account = relationship("AWSAccount", back_populates="budgets")
    alerts = relationship("BudgetAlert", back_populates="budget", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Budget {self.name} - ${self.budget_amount}/{self.period}>"


class BudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)

    # Alert details
    alert_type = Column(String, nullable=False)  # "threshold_exceeded", "forecast_breach"
    current_amount = Column(Float, nullable=False)
    budget_amount = Column(Float, nullable=False)
    percentage_used = Column(Float, nullable=False)

    # Period this alert is for
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Notification status
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sent_at = Column(DateTime, nullable=True)
    notification_channels_used = Column(JSONB, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    alert_metadata = Column(JSONB, nullable=True)  # Additional context

    # Relationships
    budget = relationship("Budget", back_populates="alerts")

    def __repr__(self):
        return f"<BudgetAlert {self.alert_type} - {self.percentage_used}% used>"
