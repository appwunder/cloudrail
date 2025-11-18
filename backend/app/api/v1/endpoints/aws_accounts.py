from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.db.base import get_db
from app.core.deps import get_current_user, get_current_tenant
from app.models.user import User
from app.models.tenant import Tenant
from app.models.aws_account import AWSAccount
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AWSAccountCreate(BaseModel):
    account_id: str
    account_name: str
    role_arn: str
    external_id: Optional[str] = None
    region: str = "us-east-1"


class AWSAccountResponse(BaseModel):
    id: uuid.UUID
    account_id: str
    account_name: Optional[str]
    role_arn: str
    region: str
    is_active: bool
    sync_status: str
    last_sync_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=AWSAccountResponse, status_code=status.HTTP_201_CREATED)
async def link_aws_account(
    account_data: AWSAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Link a new AWS account to the tenant"""

    # Check if account already exists for this tenant
    existing_account = db.query(AWSAccount).filter(
        AWSAccount.tenant_id == current_tenant.id,
        AWSAccount.account_id == account_data.account_id
    ).first()

    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AWS account already linked to this tenant"
        )

    # Create new AWS account
    new_account = AWSAccount(
        id=uuid.uuid4(),
        tenant_id=current_tenant.id,
        account_id=account_data.account_id,
        account_name=account_data.account_name,
        role_arn=account_data.role_arn,
        external_id=account_data.external_id,
        region=account_data.region,
        is_active=True,
        sync_status="pending"
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.get("/", response_model=List[AWSAccountResponse])
async def list_aws_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List all AWS accounts for the current tenant"""

    accounts = db.query(AWSAccount).filter(
        AWSAccount.tenant_id == current_tenant.id
    ).all()

    return accounts


@router.get("/{account_id}", response_model=AWSAccountResponse)
async def get_aws_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get a specific AWS account"""

    account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS account not found"
        )

    return account


@router.post("/{account_id}/sync")
async def sync_aws_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Trigger a manual sync for an AWS account"""

    account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS account not found"
        )

    # Update sync status
    account.sync_status = "syncing"
    account.last_sync_at = datetime.utcnow()
    db.commit()

    # TODO: Trigger background job to sync cost data

    return {
        "message": f"Sync triggered for account {account.account_name}",
        "account_id": str(account_id),
        "sync_status": "syncing"
    }


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_aws_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Unlink an AWS account"""

    account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS account not found"
        )

    # Soft delete - mark as inactive
    account.is_active = False
    db.commit()

    return None
