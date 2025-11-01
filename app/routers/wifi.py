from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database.database import get_db
from ..database.models import WifiCode, Booking, User, WifiUsageStatus
from ..services.wifi_service import WifiService
from .auth import get_current_user

router = APIRouter()


# ---- Schemas ----
class WifiCodeResponse(BaseModel):
    id: str
    booking_id: str
    code: str
    qr_code_data: Optional[str] = None
    expiry_time: str
    usage_status: str
    bandwidth_limit_mb: Optional[int] = None
    provider_code_id: Optional[str] = None
    created_at: str
    updated_at: str


class WifiActivationRequest(BaseModel):
    device_mac: Optional[str] = None
    device_name: Optional[str] = None


class WifiActivationResponse(BaseModel):
    success: bool
    message: str
    session_duration_minutes: Optional[int] = None
    bandwidth_remaining_mb: Optional[int] = None


class WifiUsageStats(BaseModel):
    total_usage_mb: int
    remaining_bandwidth_mb: int
    session_count: int
    last_used: Optional[str] = None


# ---- Public Endpoints ----
@router.get("/codes/{code_id}", response_model=WifiCodeResponse)
async def get_wifi_code(
    code_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    guest_email: Optional[str] = Query(None, description="Guest email for verification")
):
    """Get WiFi code details."""
    result = await session.execute(
        select(WifiCode).where(WifiCode.id == code_id)
    )
    wifi_code = result.scalar_one_or_none()
    
    if not wifi_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WiFi code not found"
        )
    
    # Check if user has access to this WiFi code
    if current_user:
        # Get booking to check user access
        booking_result = await session.execute(
            select(Booking).where(Booking.id == wifi_code.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        if booking and booking.user_id:
            if str(booking.user_id) != current_user["id"] and current_user["role"] != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    else:
        # Guest access - verify email matches booking
        if not guest_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest email is required for accessing WiFi code"
            )
        
        booking_result = await session.execute(
            select(Booking).where(Booking.id == wifi_code.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        if not booking or booking.guest_email != guest_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return WifiCodeResponse(
        id=str(wifi_code.id),
        booking_id=str(wifi_code.booking_id),
        code=wifi_code.code,
        qr_code_data=wifi_code.qr_code_data,
        expiry_time=wifi_code.expiry_time.isoformat(),
        usage_status=wifi_code.usage_status.value,
        bandwidth_limit_mb=wifi_code.bandwidth_limit_mb,
        provider_code_id=wifi_code.provider_code_id,
        created_at=wifi_code.created_at.isoformat(),
        updated_at=wifi_code.updated_at.isoformat()
    )


@router.get("/user/codes", response_model=List[WifiCodeResponse])
async def get_user_wifi_codes(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[WifiUsageStatus] = Query(None)
):
    """Get user's WiFi codes."""
    # Get user's bookings first
    bookings_result = await session.execute(
        select(Booking).where(Booking.user_id == current_user["id"])
    )
    user_bookings = bookings_result.scalars().all()
    booking_ids = [str(booking.id) for booking in user_bookings]
    
    if not booking_ids:
        return []
    
    # Get WiFi codes for user's bookings
    query = select(WifiCode).where(WifiCode.booking_id.in_(booking_ids))
    
    if status:
        query = query.where(WifiCode.usage_status == status)
    
    query = query.order_by(WifiCode.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    wifi_codes = result.scalars().all()
    
    return [
        WifiCodeResponse(
            id=str(wifi_code.id),
            booking_id=str(wifi_code.booking_id),
            code=wifi_code.code,
            qr_code_data=wifi_code.qr_code_data,
            expiry_time=wifi_code.expiry_time.isoformat(),
            usage_status=wifi_code.usage_status.value,
            bandwidth_limit_mb=wifi_code.bandwidth_limit_mb,
            provider_code_id=wifi_code.provider_code_id,
            created_at=wifi_code.created_at.isoformat(),
            updated_at=wifi_code.updated_at.isoformat()
        )
        for wifi_code in wifi_codes
    ]


@router.get("/guest/{email}/codes", response_model=List[WifiCodeResponse])
async def get_guest_wifi_codes(
    email: EmailStr,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[WifiUsageStatus] = Query(None)
):
    """Get WiFi codes for a guest email."""
    # Get guest bookings first
    guest_bookings_result = await session.execute(
        select(Booking).where(Booking.guest_email == email)
    )
    guest_bookings = guest_bookings_result.scalars().all()
    booking_ids = [booking.id for booking in guest_bookings]
    
    if not booking_ids:
        return []
    
    # Get WiFi codes for guest bookings
    query = select(WifiCode).where(WifiCode.booking_id.in_(booking_ids))
    
    if status:
        query = query.where(WifiCode.usage_status == status)
    
    query = query.order_by(WifiCode.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    wifi_codes = result.scalars().all()
    
    return [
        WifiCodeResponse(
            id=str(wifi_code.id),
            booking_id=str(wifi_code.booking_id),
            code=wifi_code.code,
            qr_code_data=wifi_code.qr_code_data,
            expiry_time=wifi_code.expiry_time.isoformat(),
            usage_status=wifi_code.usage_status.value,
            bandwidth_limit_mb=wifi_code.bandwidth_limit_mb,
            provider_code_id=wifi_code.provider_code_id,
            created_at=wifi_code.created_at.isoformat(),
            updated_at=wifi_code.updated_at.isoformat()
        )
        for wifi_code in wifi_codes
    ]


@router.get("/codes/{code_id}/qr-code")
async def get_wifi_qr_code(
    code_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get QR code for WiFi access."""
    result = await session.execute(
        select(WifiCode).where(WifiCode.id == code_id)
    )
    wifi_code = result.scalar_one_or_none()
    
    if not wifi_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WiFi code not found"
        )
    
    # Check access
    if current_user:
        booking_result = await session.execute(
            select(Booking).where(Booking.id == wifi_code.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        if booking and booking.user_id:
            if str(booking.user_id) != current_user["id"] and current_user["role"] != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    # Generate QR code data if not exists
    if not wifi_code.qr_code_data:
        qr_data = await WifiService.generate_qr_code(wifi_code.code)
        wifi_code.qr_code_data = qr_data
        wifi_code.updated_at = datetime.now(timezone.utc)
        await session.commit()
    
    return {
        "code_id": str(wifi_code.id),
        "wifi_code": wifi_code.code,
        "qr_code_data": wifi_code.qr_code_data,
        "expiry_time": wifi_code.expiry_time.isoformat(),
        "usage_instructions": [
            "Connect to 'Cheetah WiFi' network",
            f"Enter code: {wifi_code.code}",
            "Accept terms and conditions",
            "Enjoy free internet access"
        ]
    }


@router.post("/codes/{code_id}/activate", response_model=WifiActivationResponse)
async def activate_wifi_code(
    code_id: str,
    activation_request: WifiActivationRequest,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Activate a WiFi code for use."""
    result = await session.execute(
        select(WifiCode).where(WifiCode.id == code_id)
    )
    wifi_code = result.scalar_one_or_none()
    
    if not wifi_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WiFi code not found"
        )
    
    # Check if code is still valid
    if wifi_code.expiry_time < datetime.now(timezone.utc):
        wifi_code.usage_status = WifiUsageStatus.EXPIRED
        wifi_code.updated_at = datetime.now(timezone.utc)
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WiFi code has expired"
        )
    
    # Check if code is already used
    if wifi_code.usage_status == WifiUsageStatus.USED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WiFi code has already been used"
        )
    
    # Activate the code
    activation_result = await WifiService.activate_wifi_code(
        session=session,
        code_id=code_id,
        device_info=activation_request.dict()
    )
    
    if activation_result["success"]:
        # Update code status
        wifi_code.usage_status = WifiUsageStatus.ACTIVE
        wifi_code.updated_at = datetime.now(timezone.utc)
        await session.commit()
    
    return WifiActivationResponse(**activation_result)


@router.get("/codes/{code_id}/usage-stats", response_model=WifiUsageStats)
async def get_wifi_usage_stats(
    code_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get usage statistics for a WiFi code."""
    result = await session.execute(
        select(WifiCode).where(WifiCode.id == code_id)
    )
    wifi_code = result.scalar_one_or_none()
    
    if not wifi_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WiFi code not found"
        )
    
    # Check access
    if current_user:
        booking_result = await session.execute(
            select(Booking).where(Booking.id == wifi_code.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        if booking and booking.user_id:
            if str(booking.user_id) != current_user["id"] and current_user["role"] != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    # Get usage statistics (mock implementation)
    stats = await WifiService.get_usage_stats(code_id)
    
    return WifiUsageStats(**stats)


@router.get("/codes", response_model=List[WifiCodeResponse])
async def get_all_wifi_codes(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[WifiUsageStatus] = Query(None)
):
    """Get all WiFi codes (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = select(WifiCode)
    if status:
        query = query.where(WifiCode.usage_status == status)
    
    query = query.order_by(WifiCode.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    wifi_codes = result.scalars().all()
    
    return [
        WifiCodeResponse(
            id=str(wifi_code.id),
            booking_id=str(wifi_code.booking_id),
            code=wifi_code.code,
            qr_code_data=wifi_code.qr_code_data,
            expiry_time=wifi_code.expiry_time.isoformat(),
            usage_status=wifi_code.usage_status.value,
            bandwidth_limit_mb=wifi_code.bandwidth_limit_mb,
            provider_code_id=wifi_code.provider_code_id,
            created_at=wifi_code.created_at.isoformat(),
            updated_at=wifi_code.updated_at.isoformat()
        )
        for wifi_code in wifi_codes
    ]


@router.get("/statistics", response_model=Dict[str, Any])
async def get_wifi_statistics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get WiFi statistics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    stats = await WifiService.get_wifi_statistics(session)
    return stats


@router.post("/codes/{code_id}/extend")
async def extend_wifi_code(
    code_id: str,
    extension_hours: int = Query(..., ge=1, le=24),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Extend WiFi code validity (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await session.execute(
        select(WifiCode).where(WifiCode.id == code_id)
    )
    wifi_code = result.scalar_one_or_none()
    
    if not wifi_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WiFi code not found"
        )
    
    # Extend expiry time
    wifi_code.expiry_time = wifi_code.expiry_time + timedelta(hours=extension_hours)
    wifi_code.updated_at = datetime.now(timezone.utc)
    await session.commit()
    
    return {
        "message": f"WiFi code extended by {extension_hours} hours",
        "new_expiry_time": wifi_code.expiry_time.isoformat()
    }
