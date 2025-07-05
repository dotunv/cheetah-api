from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_db
from ..database.models import BookingStatus
from ..services.booking_service import BookingService
from ..services.transport_provider_service import TransportProviderService
from .auth import get_current_user

router = APIRouter()


# Pydantic models for request/response
class RouteSearchRequest(BaseModel):
    origin: str
    destination: str
    date: datetime
    max_price: Optional[float] = None
    departure_after: Optional[datetime] = None
    departure_before: Optional[datetime] = None
    providers: Optional[List[str]] = None
    vehicle_types: Optional[List[str]] = None


class PassengerDetail(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None


class BookingCreateRequest(BaseModel):
    schedule_id: str
    passenger_details: List[PassengerDetail]
    guest_email: Optional[EmailStr] = None
    guest_phone: Optional[str] = None


class BookingResponse(BaseModel):
    booking_id: str
    booking_reference: str
    provider_booking_reference: Optional[str] = None
    total_amount: float
    booking_status: str
    payment_status: str
    passenger_count: int
    schedule_details: Dict[str, Any]


class RouteSearchResponse(BaseModel):
    schedule_id: str
    provider_code: str
    provider_name: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    total_seats: int
    available_seats: int
    base_price: float
    vehicle_type: str
    amenities: List[str]


@router.get("/search", response_model=List[RouteSearchResponse])
async def search_routes(
    origin: str = Query(..., description="Origin city"),
    destination: str = Query(..., description="Destination city"),
    date: datetime = Query(..., description="Travel date"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    departure_after: Optional[datetime] = Query(None, description="Earliest departure time"),
    departure_before: Optional[datetime] = Query(None, description="Latest departure time"),
    providers: Optional[str] = Query(None, description="Comma-separated provider codes"),
    vehicle_types: Optional[str] = Query(None, description="Comma-separated vehicle types"),
    session: AsyncSession = Depends(get_db)
):
    """Search for available routes across all providers."""
    # Parse filters
    filters = {}
    if max_price:
        filters["max_price"] = max_price
    if departure_after:
        filters["departure_after"] = departure_after.isoformat()
    if departure_before:
        filters["departure_before"] = departure_before.isoformat()
    if providers:
        filters["providers"] = [p.strip() for p in providers.split(",")]
    if vehicle_types:
        filters["vehicle_types"] = [v.strip() for v in vehicle_types.split(",")]
    
    # Search routes
    routes = await BookingService.search_routes(
        session=session,
        origin=origin,
        destination=destination,
        date=date,
        filters=filters
    )
    
    return [RouteSearchResponse(**route) for route in routes]


@router.get("/schedule/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule_details(
    schedule_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific schedule."""
    schedule_details = await BookingService.get_schedule_details(session, schedule_id)
    
    if not schedule_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return schedule_details


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_request: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new booking."""
    try:
        # Convert passenger details to dict format
        passenger_details = [
            {
                "first_name": p.first_name,
                "last_name": p.last_name,
                "phone": p.phone,
                "email": p.email,
                "id_type": p.id_type,
                "id_number": p.id_number
            }
            for p in booking_request.passenger_details
        ]
        
        # Create booking
        booking = await BookingService.create_booking(
            session=session,
            schedule_id=booking_request.schedule_id,
            passenger_details=passenger_details,
            user_id=current_user["id"] if current_user else None,
            guest_email=booking_request.guest_email,
            guest_phone=booking_request.guest_phone,
            background_tasks=background_tasks
        )
        
        return BookingResponse(**booking)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking"
        )


@router.get("/{booking_id}", response_model=Dict[str, Any])
async def get_booking_details(
    booking_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get detailed booking information."""
    booking_details = await BookingService.get_booking_details(session, booking_id)
    
    if not booking_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user has permission to view this booking
    if current_user:
        user_id = current_user["id"]
        if booking_details.get("user_id") and booking_details["user_id"] != user_id:
            # Check if user is admin
            if current_user["role"] != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    return booking_details


@router.get("/user/bookings", response_model=List[Dict[str, Any]])
async def get_user_bookings(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None)
):
    """Get current user's booking history."""
    user_id = current_user["id"]
    bookings = await BookingService.get_user_bookings(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status
    )
    
    return bookings


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Cancel a booking."""
    user_id = current_user["id"] if current_user else None
    
    success = await BookingService.cancel_booking(
        session=session,
        booking_id=booking_id,
        user_id=user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or cannot be cancelled"
        )
    
    return {"message": "Booking cancelled successfully"}


@router.get("/reference/{booking_reference}", response_model=Dict[str, Any])
async def get_booking_by_reference(
    booking_reference: str,
    session: AsyncSession = Depends(get_db)
):
    """Get booking details by booking reference (for guest bookings)."""
    # This would need to be implemented in the service
    # For now, we'll return a mock response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is not yet implemented"
    )


@router.get("/providers/statistics", response_model=Dict[str, Any])
async def get_provider_statistics(
    session: AsyncSession = Depends(get_db)
):
    """Get transport provider statistics."""
    stats = await TransportProviderService.get_route_statistics(session)
    return stats


@router.get("/statistics", response_model=Dict[str, Any])
async def get_booking_statistics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get booking statistics (admin only)."""
    # Check if user is admin
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    stats = await BookingService.get_booking_statistics(session)
    return stats


# Admin endpoints
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


@router.get("/admin/all", response_model=List[Dict[str, Any]])
async def get_all_bookings(
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None)
):
    """Get all bookings (admin only)."""
    # This would need to be implemented in the service
    # For now, we'll return a mock response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is not yet implemented"
    )


@router.post("/admin/{booking_id}/confirm")
async def confirm_booking_admin(
    booking_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Confirm a booking (admin only)."""
    # This would need to be implemented in the service
    # For now, we'll return a mock response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is not yet implemented"
    ) 