from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date, timedelta
import uuid
import logging

from app.db.base import get_db
from app.core.deps import get_current_user, get_current_tenant
from app.models.user import User
from app.models.tenant import Tenant
from app.models.cloud_account import CloudAccount, CloudProvider
from app.models.cost_data import MultiCloudCostData
from app.schemas.cloud_account import (
    CloudAccountCreate,
    CloudAccountUpdate,
    CloudAccountResponse,
    CloudAccountListResponse,
    CloudAccountSyncRequest,
    CloudAccountSyncResponse
)
from app.services.cloud_providers import CloudProviderServiceFactory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=CloudAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_cloud_account(
    account_data: CloudAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Link a new cloud account to the tenant"""

    # Check if account already exists for this tenant and provider
    existing_account = db.query(CloudAccount).filter(
        CloudAccount.tenant_id == current_tenant.id,
        CloudAccount.provider == account_data.provider,
        CloudAccount.account_id == account_data.account_id
    ).first()

    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{account_data.provider.value.upper()} account already linked to this tenant"
        )

    # Create new cloud account
    new_account = CloudAccount(
        id=uuid.uuid4(),
        tenant_id=current_tenant.id,
        provider=account_data.provider,
        account_id=account_data.account_id,
        account_name=account_data.account_name,
        credentials=account_data.credentials,  # Note: Should be encrypted in production
        region=account_data.region,
        currency=account_data.currency,
        is_active=True,
        sync_status="pending",
        config_data=account_data.config_data
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.get("/", response_model=CloudAccountListResponse)
async def list_cloud_accounts(
    provider: CloudProvider = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List all cloud accounts for the current tenant"""

    query = db.query(CloudAccount).filter(
        CloudAccount.tenant_id == current_tenant.id
    )

    # Apply filters if provided
    if provider:
        query = query.filter(CloudAccount.provider == provider)

    if is_active is not None:
        query = query.filter(CloudAccount.is_active == is_active)

    accounts = query.order_by(CloudAccount.created_at.desc()).all()

    return CloudAccountListResponse(
        accounts=accounts,
        total=len(accounts)
    )


@router.get("/{account_id}", response_model=CloudAccountResponse)
async def get_cloud_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get a specific cloud account"""

    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id,
        CloudAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found"
        )

    return account


@router.put("/{account_id}", response_model=CloudAccountResponse)
async def update_cloud_account(
    account_id: uuid.UUID,
    account_update: CloudAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Update a cloud account"""

    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id,
        CloudAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found"
        )

    # Update fields if provided
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


@router.post("/{account_id}/sync", response_model=CloudAccountSyncResponse)
async def sync_cloud_account(
    account_id: uuid.UUID,
    sync_request: CloudAccountSyncRequest = CloudAccountSyncRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Trigger a manual sync for a cloud account"""

    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id,
        CloudAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found"
        )

    # Check if recently synced (unless force=True)
    if not sync_request.force and account.last_sync_at:
        time_since_sync = datetime.utcnow() - account.last_sync_at.replace(tzinfo=None)
        if time_since_sync.total_seconds() < 300:  # 5 minutes
            return CloudAccountSyncResponse(
                account_id=account.id,
                provider=account.provider,
                sync_status=account.sync_status,
                message=f"Account was recently synced. Use force=true to sync again.",
                last_sync_at=account.last_sync_at
            )

    # Update sync status to syncing
    account.sync_status = "syncing"
    account.last_sync_at = datetime.utcnow()
    account.sync_error = None
    db.commit()

    try:
        # Create cloud provider service
        logger.info(f"Creating {account.provider.value} service for account {account.account_id}")
        service = CloudProviderServiceFactory.create_service(
            provider=account.provider,
            credentials=account.credentials,
            account_id=account.account_id,
            region=account.region
        )

        # Fetch costs for the last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        logger.info(f"Fetching costs from {start_date} to {end_date}")

        with service:
            cost_records = service.fetch_costs(
                start_date=start_date,
                end_date=end_date,
                granularity="daily"
            )

        # Store cost records in database
        logger.info(f"Storing {len(cost_records)} cost records")
        stored_count = 0

        for record in cost_records:
            # Check if record already exists (idempotency)
            existing = db.query(MultiCloudCostData).filter(
                MultiCloudCostData.cloud_account_id == account.id,
                MultiCloudCostData.date == record.date,
                MultiCloudCostData.service_name == record.service_name,
                MultiCloudCostData.region == record.region
            ).first()

            if existing:
                # Update existing record
                existing.cost = record.cost
                existing.currency = record.currency
                existing.usage_quantity = record.usage_quantity
                existing.usage_unit = record.usage_unit
                existing.tags = record.tags
                existing.provider_metadata = record.provider_metadata
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                cost_data = MultiCloudCostData(
                    id=uuid.uuid4(),
                    tenant_id=current_tenant.id,
                    cloud_account_id=account.id,
                    provider=account.provider,
                    date=record.date,
                    service_name=record.service_name,
                    service_category=record.service_category,
                    resource_id=record.resource_id,
                    resource_name=record.resource_name,
                    region=record.region,
                    cost=record.cost,
                    currency=record.currency,
                    usage_quantity=record.usage_quantity,
                    usage_unit=record.usage_unit,
                    tags=record.tags,
                    provider_metadata=record.provider_metadata
                )
                db.add(cost_data)
                stored_count += 1

        db.commit()

        # Update sync status to success
        account.sync_status = "success"
        account.last_sync_at = datetime.utcnow()
        account.sync_error = None
        db.commit()

        logger.info(f"Successfully synced {stored_count} new cost records for {account.provider.value} account")

        return CloudAccountSyncResponse(
            account_id=account.id,
            provider=account.provider,
            sync_status="success",
            message=f"Successfully synced {stored_count} cost records from {account.provider.value.upper()}",
            last_sync_at=account.last_sync_at
        )

    except Exception as e:
        # Update sync status to error
        error_message = str(e)
        logger.error(f"Sync failed for {account.provider.value} account: {error_message}")

        account.sync_status = "error"
        account.sync_error = error_message
        account.last_sync_at = datetime.utcnow()
        db.commit()

        return CloudAccountSyncResponse(
            account_id=account.id,
            provider=account.provider,
            sync_status="error",
            message=f"Sync failed: {error_message}",
            last_sync_at=account.last_sync_at
        )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cloud_account(
    account_id: uuid.UUID,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Delete a cloud account (soft delete by default)"""

    account = db.query(CloudAccount).filter(
        CloudAccount.id == account_id,
        CloudAccount.tenant_id == current_tenant.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found"
        )

    if hard_delete:
        # Hard delete - remove from database
        db.delete(account)
    else:
        # Soft delete - mark as inactive
        account.is_active = False

    db.commit()

    return None


@router.get("/providers/summary")
async def get_providers_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get summary of cloud accounts by provider"""

    accounts = db.query(CloudAccount).filter(
        CloudAccount.tenant_id == current_tenant.id,
        CloudAccount.is_active == True
    ).all()

    # Group by provider
    summary = {}
    for provider in CloudProvider:
        provider_accounts = [a for a in accounts if a.provider == provider]
        summary[provider.value] = {
            "count": len(provider_accounts),
            "accounts": [
                {
                    "id": str(a.id),
                    "account_id": a.account_id,
                    "account_name": a.account_name,
                    "sync_status": a.sync_status,
                    "last_sync_at": a.last_sync_at
                }
                for a in provider_accounts
            ]
        }

    return {
        "total_accounts": len(accounts),
        "by_provider": summary
    }
