from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.architecture import Architecture
from app.schemas.architecture import (
    ArchitectureCreate,
    ArchitectureUpdate,
    ArchitectureResponse,
    ArchitectureListResponse
)

router = APIRouter()


@router.post("", response_model=ArchitectureResponse, status_code=status.HTTP_201_CREATED)
def create_architecture(
    architecture: ArchitectureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new architecture design"""
    db_architecture = Architecture(
        tenant_id=current_user.tenant_id,
        name=architecture.name,
        description=architecture.description,
        nodes=architecture.nodes,
        edges=architecture.edges,
        estimated_monthly_cost=architecture.estimated_monthly_cost,
        is_public=architecture.is_public
    )
    db.add(db_architecture)
    db.commit()
    db.refresh(db_architecture)
    return db_architecture


@router.get("", response_model=ArchitectureListResponse)
def list_architectures(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all architectures for the current tenant"""
    query = db.query(Architecture).filter(
        Architecture.tenant_id == current_user.tenant_id
    )

    total = query.count()
    architectures = query.order_by(Architecture.updated_at.desc()).offset(skip).limit(limit).all()

    return {
        "architectures": architectures,
        "total": total
    }


@router.get("/{architecture_id}", response_model=ArchitectureResponse)
def get_architecture(
    architecture_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific architecture by ID"""
    architecture = db.query(Architecture).filter(
        Architecture.id == architecture_id,
        Architecture.tenant_id == current_user.tenant_id
    ).first()

    if not architecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Architecture not found"
        )

    return architecture


@router.put("/{architecture_id}", response_model=ArchitectureResponse)
def update_architecture(
    architecture_id: UUID,
    architecture_update: ArchitectureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an architecture"""
    db_architecture = db.query(Architecture).filter(
        Architecture.id == architecture_id,
        Architecture.tenant_id == current_user.tenant_id
    ).first()

    if not db_architecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Architecture not found"
        )

    # Update only provided fields
    update_data = architecture_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_architecture, field, value)

    db.commit()
    db.refresh(db_architecture)
    return db_architecture


@router.delete("/{architecture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_architecture(
    architecture_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an architecture"""
    db_architecture = db.query(Architecture).filter(
        Architecture.id == architecture_id,
        Architecture.tenant_id == current_user.tenant_id
    ).first()

    if not db_architecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Architecture not found"
        )

    db.delete(db_architecture)
    db.commit()
    return None


@router.post("/{architecture_id}/duplicate", response_model=ArchitectureResponse, status_code=status.HTTP_201_CREATED)
def duplicate_architecture(
    architecture_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Duplicate an existing architecture"""
    original = db.query(Architecture).filter(
        Architecture.id == architecture_id,
        Architecture.tenant_id == current_user.tenant_id
    ).first()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Architecture not found"
        )

    # Create duplicate
    duplicate = Architecture(
        tenant_id=current_user.tenant_id,
        name=f"{original.name} (Copy)",
        description=original.description,
        nodes=original.nodes,
        edges=original.edges,
        estimated_monthly_cost=original.estimated_monthly_cost,
        is_public=False
    )

    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate
