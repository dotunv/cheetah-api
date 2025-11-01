from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database.database import get_db
from ..database.models import InsurancePolicy, Booking, User, InsuranceStatus
from ..services.insurance_service import InsuranceService
from .auth import get_current_user

router = APIRouter()


# ---- Schemas ----
class InsurancePolicyResponse(BaseModel):
    id: str
    booking_id: str
    policy_number: str
    coverage_details_url: Optional[str] = None
    status: str
    start_date: str
    end_date: str
    coverage_amount: float
    provider_policy_id: Optional[str] = None
    created_at: str
    updated_at: str


class InsuranceClaimRequest(BaseModel):
    claim_type: str
    description: str
    incident_date: datetime
    amount_claimed: Optional[float] = None
    supporting_documents: Optional[List[str]] = None


class InsuranceClaimResponse(BaseModel):
    claim_id: str
    policy_id: str
    status: str
    claim_number: str
    submitted_at: str
    estimated_processing_time: str


# ---- Public Endpoints ----
@router.get("/policies/{policy_id}", response_model=InsurancePolicyResponse)
async def get_insurance_policy(
    policy_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    guest_email: Optional[str] = Query(None, description="Guest email for verification")
):
    """Get single insurance policy details."""
    result = await session.execute(
        select(InsurancePolicy).where(InsurancePolicy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance policy not found"
        )
    
    # Check if user has access to this policy
    if current_user:
        if str(policy.user_id) != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    else:
        # Guest access - verify email matches booking
        if not guest_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest email is required for accessing insurance policy"
            )
        
        # Get booking details to verify guest email
        booking_result = await session.execute(
            select(Booking).where(Booking.id == policy.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        if not booking or booking.guest_email != guest_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return InsurancePolicyResponse(
        id=str(policy.id),
        booking_id=str(policy.booking_id),
        policy_number=policy.policy_number,
        coverage_details_url=policy.coverage_details_url,
        status=policy.status.value,
        start_date=policy.start_date.isoformat(),
        end_date=policy.end_date.isoformat(),
        coverage_amount=policy.coverage_amount,
        provider_policy_id=policy.provider_policy_id,
        created_at=policy.created_at.isoformat(),
        updated_at=policy.updated_at.isoformat()
    )


@router.get("/user/policies", response_model=List[InsurancePolicyResponse])
async def get_user_insurance_policies(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[InsuranceStatus] = Query(None)
):
    """Get user's insurance policies."""
    query = select(InsurancePolicy).where(InsurancePolicy.user_id == current_user["id"])
    
    if status:
        query = query.where(InsurancePolicy.status == status)
    
    query = query.order_by(InsurancePolicy.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    policies = result.scalars().all()
    
    return [
        InsurancePolicyResponse(
            id=str(policy.id),
            booking_id=str(policy.booking_id),
            policy_number=policy.policy_number,
            coverage_details_url=policy.coverage_details_url,
            status=policy.status.value,
            start_date=policy.start_date.isoformat(),
            end_date=policy.end_date.isoformat(),
            coverage_amount=policy.coverage_amount,
            provider_policy_id=policy.provider_policy_id,
            created_at=policy.created_at.isoformat(),
            updated_at=policy.updated_at.isoformat()
        )
        for policy in policies
    ]


@router.get("/guest/{email}/policies", response_model=List[InsurancePolicyResponse])
async def get_guest_insurance_policies(
    email: EmailStr,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[InsuranceStatus] = Query(None)
):
    """Get insurance policies for a guest email."""
    # Get guest bookings first
    guest_bookings_result = await session.execute(
        select(Booking).where(Booking.guest_email == email)
    )
    guest_bookings = guest_bookings_result.scalars().all()
    booking_ids = [booking.id for booking in guest_bookings]
    
    if not booking_ids:
        return []
    
    # Get insurance policies for guest bookings
    query = select(InsurancePolicy).where(InsurancePolicy.booking_id.in_(booking_ids))
    
    if status:
        query = query.where(InsurancePolicy.status == status)
    
    query = query.order_by(InsurancePolicy.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    policies = result.scalars().all()
    
    return [
        InsurancePolicyResponse(
            id=str(policy.id),
            booking_id=str(policy.booking_id),
            policy_number=policy.policy_number,
            coverage_details_url=policy.coverage_details_url,
            status=policy.status.value,
            start_date=policy.start_date.isoformat(),
            end_date=policy.end_date.isoformat(),
            coverage_amount=policy.coverage_amount,
            provider_policy_id=policy.provider_policy_id,
            created_at=policy.created_at.isoformat(),
            updated_at=policy.updated_at.isoformat()
        )
        for policy in policies
    ]


@router.get("/policies", response_model=List[InsurancePolicyResponse])
async def get_all_insurance_policies(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[InsuranceStatus] = Query(None)
):
    """Get all insurance policies (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = select(InsurancePolicy)
    if status:
        query = query.where(InsurancePolicy.status == status)
    
    query = query.order_by(InsurancePolicy.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    policies = result.scalars().all()
    
    return [
        InsurancePolicyResponse(
            id=str(policy.id),
            booking_id=str(policy.booking_id),
            policy_number=policy.policy_number,
            coverage_details_url=policy.coverage_details_url,
            status=policy.status.value,
            start_date=policy.start_date.isoformat(),
            end_date=policy.end_date.isoformat(),
            coverage_amount=policy.coverage_amount,
            provider_policy_id=policy.provider_policy_id,
            created_at=policy.created_at.isoformat(),
            updated_at=policy.updated_at.isoformat()
        )
        for policy in policies
    ]


@router.post("/policies/{policy_id}/claim", response_model=InsuranceClaimResponse)
async def submit_insurance_claim(
    policy_id: str,
    claim_request: InsuranceClaimRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Submit an insurance claim for a policy."""
    # Verify policy exists and belongs to user
    result = await session.execute(
        select(InsurancePolicy).where(InsurancePolicy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance policy not found"
        )
    
    if str(policy.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if policy is active
    if policy.status != InsuranceStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit claim for inactive policy"
        )
    
    # Submit claim (mock implementation)
    claim_data = await InsuranceService.submit_claim(
        session=session,
        policy_id=policy_id,
        user_id=current_user["id"],
        claim_details=claim_request.dict()
    )
    
    return InsuranceClaimResponse(**claim_data)


@router.get("/policies/{policy_id}/coverage-details")
async def get_coverage_details(
    policy_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get detailed coverage information for a policy."""
    result = await session.execute(
        select(InsurancePolicy).where(InsurancePolicy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance policy not found"
        )
    
    # Check access
    if current_user:
        if str(policy.user_id) != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Get coverage details (mock implementation)
    coverage_details = await InsuranceService.get_coverage_details(policy_id)
    
    return {
        "policy_id": policy_id,
        "policy_number": policy.policy_number,
        "coverage_amount": policy.coverage_amount,
        "coverage_period": {
            "start_date": policy.start_date.isoformat(),
            "end_date": policy.end_date.isoformat()
        },
        "coverage_details": coverage_details,
        "terms_and_conditions": "https://example.com/insurance-terms",
        "contact_info": {
            "claims_hotline": "+1-800-INSURANCE",
            "email": "claims@insurance.com"
        }
    }


@router.get("/statistics", response_model=Dict[str, Any])
async def get_insurance_statistics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get insurance statistics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    stats = await InsuranceService.get_insurance_statistics(session)
    return stats
