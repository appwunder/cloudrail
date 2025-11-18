from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.budget import Budget, BudgetAlert
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetListResponse,
    BudgetStatusResponse,
    BudgetAlertResponse
)
from app.services.budget_service import BudgetService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=BudgetResponse, status_code=201)
def create_budget(
    budget_in: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new budget"""
    try:
        # Create budget
        budget = Budget(
            tenant_id=current_user.tenant_id,
            **budget_in.model_dump()
        )

        db.add(budget)
        db.commit()
        db.refresh(budget)

        logger.info(f"Created budget {budget.id} for tenant {current_user.tenant_id}")

        # Return enriched response with current status
        return BudgetService.enrich_budget_response(budget, db)

    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating budget: {str(e)}")


@router.get("/", response_model=BudgetListResponse)
def list_budgets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    account_id: Optional[UUID] = Query(None, description="Filter by account"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all budgets for the current tenant"""
    try:
        # Build query
        query = db.query(Budget).filter(Budget.tenant_id == current_user.tenant_id)

        # Apply filters
        if is_active is not None:
            query = query.filter(Budget.is_active == is_active)
        if account_id:
            query = query.filter(Budget.account_id == account_id)

        # Get total count
        total = query.count()

        # Paginate
        budgets = query.order_by(Budget.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        # Enrich with current status
        enriched_budgets = [BudgetService.enrich_budget_response(budget, db) for budget in budgets]

        return BudgetListResponse(
            budgets=enriched_budgets,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing budgets: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing budgets: {str(e)}")


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific budget by ID"""
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.tenant_id == current_user.tenant_id
        )
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return BudgetService.enrich_budget_response(budget, db)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: UUID,
    budget_in: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a budget"""
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.tenant_id == current_user.tenant_id
        )
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        # Update fields
        update_data = budget_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(budget, field, value)

        db.commit()
        db.refresh(budget)

        logger.info(f"Updated budget {budget_id}")

        return BudgetService.enrich_budget_response(budget, db)

    except Exception as e:
        logger.error(f"Error updating budget: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating budget: {str(e)}")


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a budget"""
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.tenant_id == current_user.tenant_id
        )
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        db.delete(budget)
        db.commit()
        logger.info(f"Deleted budget {budget_id}")
        return None

    except Exception as e:
        logger.error(f"Error deleting budget: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting budget: {str(e)}")


@router.get("/{budget_id}/status", response_model=BudgetStatusResponse)
def get_budget_status(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed status for a specific budget"""
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.tenant_id == current_user.tenant_id
        )
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        status = BudgetService.check_budget(db, budget)
        return status

    except Exception as e:
        logger.error(f"Error checking budget status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking budget status: {str(e)}")


@router.get("/{budget_id}/alerts", response_model=List[BudgetAlertResponse])
def get_budget_alerts(
    budget_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alerts for a specific budget"""
    # Verify budget belongs to user's tenant
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.tenant_id == current_user.tenant_id
        )
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    alerts = db.query(BudgetAlert).filter(
        BudgetAlert.budget_id == budget_id
    ).order_by(BudgetAlert.created_at.desc()).limit(limit).all()

    return alerts


@router.post("/check-all", response_model=List[BudgetStatusResponse])
def check_all_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check status of all active budgets for the current tenant"""
    try:
        statuses = BudgetService.check_all_budgets(db, current_user.tenant_id)
        return statuses

    except Exception as e:
        logger.error(f"Error checking budgets: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking budgets: {str(e)}")


@router.post("/{budget_id}/test-alert", response_model=BudgetAlertResponse)
def test_budget_alert(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test budget alert creation (for testing purposes)"""
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.tenant_id == current_user.tenant_id
        )
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        # Check budget status
        status = BudgetService.check_budget(db, budget)

        # Create alert if needed
        alert = BudgetService.create_alert_if_needed(db, budget, status)

        if not alert:
            raise HTTPException(status_code=200, detail="Budget is within threshold, no alert created")

        return alert

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing alert: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing alert: {str(e)}")
