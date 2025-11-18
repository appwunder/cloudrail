from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from app.models.budget import Budget, BudgetAlert, BudgetPeriod
from app.models.cost_data import CostData
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetStatusResponse

logger = logging.getLogger(__name__)


class BudgetService:
    """Service for managing budgets and monitoring spending"""

    @staticmethod
    def get_period_dates(period: BudgetPeriod, reference_date: datetime = None) -> tuple[datetime, datetime]:
        """Calculate start and end dates for a budget period"""
        if reference_date is None:
            reference_date = datetime.utcnow()

        if period == BudgetPeriod.DAILY:
            start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == BudgetPeriod.WEEKLY:
            start = reference_date - timedelta(days=reference_date.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == BudgetPeriod.MONTHLY:
            start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        elif period == BudgetPeriod.QUARTERLY:
            quarter = (reference_date.month - 1) // 3
            start = reference_date.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next quarter
            end_month = start.month + 3
            if end_month > 12:
                end = start.replace(year=start.year + 1, month=end_month - 12)
            else:
                end = start.replace(month=end_month)
        elif period == BudgetPeriod.ANNUALLY:
            start = reference_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        else:
            raise ValueError(f"Unsupported period: {period}")

        return start, end

    @staticmethod
    def get_current_spend(
        db: Session,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
        account_id: Optional[UUID] = None,
        service_name: Optional[str] = None,
        region: Optional[str] = None
    ) -> float:
        """Calculate current spending for a budget"""
        query = db.query(func.sum(CostData.cost)).filter(
            and_(
                CostData.tenant_id == tenant_id,
                CostData.date >= period_start,
                CostData.date < period_end
            )
        )

        # Apply optional filters
        if account_id:
            query = query.filter(CostData.account_id == account_id)
        if service_name:
            query = query.filter(CostData.service == service_name)
        if region:
            query = query.filter(CostData.region == region)

        result = query.scalar()
        return float(result) if result else 0.0

    @staticmethod
    def calculate_budget_status(
        budget: Budget,
        current_spend: float,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate detailed budget status"""
        now = datetime.utcnow()

        # Calculate days
        total_days = (period_end - period_start).days
        days_elapsed = (now - period_start).days
        days_remaining = (period_end - now).days

        # Ensure days_elapsed is at least 1 to avoid division by zero
        days_elapsed = max(days_elapsed, 1)

        # Calculate percentages
        percentage_used = (current_spend / budget.budget_amount * 100) if budget.budget_amount > 0 else 0
        is_over_threshold = percentage_used >= budget.threshold_percentage
        is_over_budget = current_spend >= budget.budget_amount

        # Project future spend
        daily_average = current_spend / days_elapsed
        projected_spend = daily_average * total_days if days_elapsed > 0 else 0
        will_exceed_budget = projected_spend > budget.budget_amount

        return {
            "budget_id": budget.id,
            "budget_name": budget.name,
            "budget_amount": budget.budget_amount,
            "current_spend": current_spend,
            "percentage_used": round(percentage_used, 2),
            "threshold_percentage": budget.threshold_percentage,
            "is_over_threshold": is_over_threshold,
            "is_over_budget": is_over_budget,
            "days_into_period": days_elapsed,
            "days_remaining": max(days_remaining, 0),
            "projected_spend": round(projected_spend, 2),
            "will_exceed_budget": will_exceed_budget
        }

    @staticmethod
    def check_budget(db: Session, budget: Budget) -> BudgetStatusResponse:
        """Check a budget's current status"""
        period_start, period_end = BudgetService.get_period_dates(budget.period)

        current_spend = BudgetService.get_current_spend(
            db=db,
            tenant_id=budget.tenant_id,
            period_start=period_start,
            period_end=period_end,
            account_id=budget.account_id,
            service_name=budget.service_name,
            region=budget.region
        )

        status = BudgetService.calculate_budget_status(
            budget=budget,
            current_spend=current_spend,
            period_start=period_start,
            period_end=period_end
        )

        return BudgetStatusResponse(**status)

    @staticmethod
    def check_all_budgets(db: Session, tenant_id: UUID) -> List[BudgetStatusResponse]:
        """Check status of all active budgets for a tenant"""
        budgets = db.query(Budget).filter(
            and_(
                Budget.tenant_id == tenant_id,
                Budget.is_active == True
            )
        ).all()

        statuses = []
        for budget in budgets:
            try:
                status = BudgetService.check_budget(db, budget)
                statuses.append(status)
            except Exception as e:
                logger.error(f"Error checking budget {budget.id}: {e}")
                continue

        return statuses

    @staticmethod
    def create_alert_if_needed(
        db: Session,
        budget: Budget,
        status: BudgetStatusResponse
    ) -> Optional[BudgetAlert]:
        """Create a budget alert if threshold is exceeded"""
        if not status.is_over_threshold:
            return None

        period_start, period_end = BudgetService.get_period_dates(budget.period)

        # Check if we already sent an alert for this period
        existing_alert = db.query(BudgetAlert).filter(
            and_(
                BudgetAlert.budget_id == budget.id,
                BudgetAlert.period_start == period_start,
                BudgetAlert.period_end == period_end,
                BudgetAlert.notification_sent == True
            )
        ).first()

        if existing_alert:
            logger.info(f"Alert already sent for budget {budget.id} in this period")
            return None

        # Determine alert type
        alert_type = "budget_exceeded" if status.is_over_budget else "threshold_exceeded"

        # Create alert
        alert = BudgetAlert(
            budget_id=budget.id,
            alert_type=alert_type,
            current_amount=status.current_spend,
            budget_amount=status.budget_amount,
            percentage_used=status.percentage_used,
            period_start=period_start,
            period_end=period_end,
            notification_sent=False
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        logger.info(f"Created alert {alert.id} for budget {budget.id} - {alert_type}")
        return alert

    @staticmethod
    def enrich_budget_response(
        budget: Budget,
        db: Session
    ) -> BudgetResponse:
        """Enrich budget with current status information"""
        period_start, period_end = BudgetService.get_period_dates(budget.period)

        current_spend = BudgetService.get_current_spend(
            db=db,
            tenant_id=budget.tenant_id,
            period_start=period_start,
            period_end=period_end,
            account_id=budget.account_id,
            service_name=budget.service_name,
            region=budget.region
        )

        now = datetime.utcnow()
        days_remaining = (period_end - now).days

        percentage_used = (current_spend / budget.budget_amount * 100) if budget.budget_amount > 0 else 0
        is_over_threshold = percentage_used >= budget.threshold_percentage
        is_over_budget = current_spend >= budget.budget_amount

        # Convert to dict and add calculated fields
        budget_dict = {
            "id": budget.id,
            "tenant_id": budget.tenant_id,
            "account_id": budget.account_id,
            "name": budget.name,
            "description": budget.description,
            "budget_amount": budget.budget_amount,
            "period": budget.period,
            "service_name": budget.service_name,
            "region": budget.region,
            "threshold_percentage": budget.threshold_percentage,
            "notification_channels": budget.notification_channels,
            "notification_emails": budget.notification_emails,
            "slack_webhook_url": budget.slack_webhook_url,
            "custom_webhook_url": budget.custom_webhook_url,
            "is_active": budget.is_active,
            "last_alert_sent_at": budget.last_alert_sent_at,
            "created_at": budget.created_at,
            "updated_at": budget.updated_at,
            # Calculated fields
            "current_spend": current_spend,
            "percentage_used": round(percentage_used, 2),
            "days_remaining": max(days_remaining, 0),
            "is_over_budget": is_over_budget,
            "is_over_threshold": is_over_threshold
        }

        return BudgetResponse(**budget_dict)
