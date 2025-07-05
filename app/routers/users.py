from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_db
from ..database.models import BookingStatus
from ..services.auth_service import AuthService
from ..services.user_service import UserService
from .auth import get_current_user

router = APIRouter()


# Pydantic models for request/response
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserBookingResponse(BaseModel):
    id: str
    booking_reference: str
    schedule_id: str
    passenger_count: int
    total_amount: float
    booking_status: str
    payment_status: str
    created_at: str
    provider_booking_reference: Optional[str] = None
    notes: Optional[str] = None


class UserInsurancePolicyResponse(BaseModel):
    id: str
    booking_id: str
    policy_number: str
    coverage_details_url: Optional[str] = None
    status: str
    start_date: str
    end_date: str
    coverage_amount: float
    created_at: str


class UserWifiCodeResponse(BaseModel):
    id: str
    booking_id: str
    code: str
    qr_code_data: Optional[str] = None
    expiry_time: str
    usage_status: str
    bandwidth_limit_mb: Optional[int] = None
    created_at: str


class UserSearchResponse(BaseModel):
    id: str
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: str


@router.get("/profile", response_model=dict)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get current user's profile with statistics."""
    user_id = current_user["id"]
    profile = await UserService.get_user_profile(session, user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile


@router.put("/profile", response_model=dict)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    user_id = current_user["id"]
    
    updated_user = await UserService.update_user_profile(
        session=session,
        user_id=user_id,
        first_name=profile_update.first_name,
        last_name=profile_update.last_name,
        phone=profile_update.phone
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return updated profile
    profile = await UserService.get_user_profile(session, user_id)
    return profile


@router.get("/bookings", response_model=List[UserBookingResponse])
async def get_user_bookings(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None)
):
    """Get current user's booking history."""
    user_id = current_user["id"]
    bookings = await UserService.get_user_bookings(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status
    )
    
    return [UserBookingResponse(**booking) for booking in bookings]


@router.get("/insurance-policies", response_model=List[UserInsurancePolicyResponse])
async def get_user_insurance_policies(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get current user's insurance policies."""
    user_id = current_user["id"]
    policies = await UserService.get_user_insurance_policies(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return [UserInsurancePolicyResponse(**policy) for policy in policies]


@router.get("/wifi-codes", response_model=List[UserWifiCodeResponse])
async def get_user_wifi_codes(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get current user's WiFi codes."""
    user_id = current_user["id"]
    wifi_codes = await UserService.get_user_wifi_codes(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return [UserWifiCodeResponse(**wifi_code) for wifi_code in wifi_codes]


@router.get("/guest/{email}", response_model=dict)
async def get_guest_user_info(
    email: EmailStr,
    session: AsyncSession = Depends(get_db)
):
    """Get guest user information by email."""
    guest_info = await UserService.get_user_by_guest_email(session, email)
    
    if not guest_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest user not found"
        )
    
    return guest_info


# Admin endpoints (require admin role)
async def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user and verify admin role."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/admin/search", response_model=List[UserSearchResponse])
async def search_users(
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
    email: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search users by various criteria (admin only)."""
    users = await UserService.search_users(
        session=session,
        email=email,
        phone=phone,
        name=name,
        limit=limit,
        offset=offset
    )
    
    return [UserSearchResponse(**user) for user in users]


@router.get("/admin/{user_id}", response_model=dict)
async def get_user_by_id(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user profile by ID (admin only)."""
    profile = await UserService.get_user_profile(session, user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return profile


@router.get("/admin/{user_id}/bookings", response_model=List[UserBookingResponse])
async def get_user_bookings_admin(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None)
):
    """Get user's booking history (admin only)."""
    bookings = await UserService.get_user_bookings(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status
    )
    
    return [UserBookingResponse(**booking) for booking in bookings]


@router.post("/admin/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Deactivate a user account (admin only)."""
    success = await AuthService.deactivate_user(session, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deactivated successfully"}


@router.post("/admin/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Activate a user account (admin only)."""
    success = await AuthService.activate_user(session, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User activated successfully"}
