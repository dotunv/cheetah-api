from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_db
from ..database.models import BookingStatus
from ..services.booking_service import BookingService
from ..services.audit_service import AuditService
from ..services.transport_provider_service import TransportProviderService
from .auth import get_current_user

router = APIRouter()


# ---- Schemas ----
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


# ---- Public Endpoints ----
@router.get("/search")
async def search_routes(
    origin: str = Query(..., description="Origin city"),
    destination: str = Query(..., description="Destination city"),
    date: datetime = Query(..., description="Travel date"),
    max_price: Optional[float] = Query(None),
    min_price: Optional[float] = Query(None),
    departure_after: Optional[datetime] = Query(None),
    departure_before: Optional[datetime] = Query(None),
    providers: Optional[str] = Query(None, description="Comma-separated provider codes"),
    vehicle_types: Optional[str] = Query(None, description="Comma-separated vehicle types"),
    sort_by: str = Query("departure_time"),
    include_comparison: bool = Query(False),
    session: AsyncSession = Depends(get_db),
):
    filters: Dict[str, Any] = {"sort_by": sort_by}
    if max_price is not None:
        filters["max_price"] = max_price
    if min_price is not None:
        filters["min_price"] = min_price
    if departure_after is not None:
        filters["departure_after"] = departure_after.isoformat()
    if departure_before is not None:
        filters["departure_before"] = departure_before.isoformat()
    if providers:
        filters["providers"] = [p.strip() for p in providers.split(",")]
    if vehicle_types:
        filters["vehicle_types"] = [v.strip() for v in vehicle_types.split(",")]

    routes = await BookingService.search_routes(
        session=session,
        origin=origin,
        destination=destination,
        date=date,
        filters=filters,
    )

    response: Dict[str, Any] = {
        "routes": [RouteSearchResponse(**route) for route in routes]
    }

    if include_comparison:
        comparison_summary = TransportProviderService.get_price_comparison_summary(routes)
        response["comparison_summary"] = comparison_summary

    return response


@router.get("/schedule/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule_details(schedule_id: str, session: AsyncSession = Depends(get_db)):
    details = await BookingService.get_schedule_details(session, schedule_id)
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return details


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_request: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        passenger_details = [
            {
                "first_name": p.first_name,
                "last_name": p.last_name,
                "phone": p.phone,
                "email": p.email,
                "id_type": p.id_type,
                "id_number": p.id_number,
            }
            for p in booking_request.passenger_details
        ]

        booking = await BookingService.create_booking(
            session=session,
            schedule_id=booking_request.schedule_id,
            passenger_details=passenger_details,
            user_id=current_user["id"] if current_user else None,
            guest_email=booking_request.guest_email,
            guest_phone=booking_request.guest_phone,
            background_tasks=background_tasks,
        )
        return BookingResponse(**booking)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create booking")


@router.get("/{booking_id}", response_model=Dict[str, Any])
async def get_booking_details(
    booking_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    guest_email: Optional[str] = Query(None, description="Guest email for verification")
):
    details = await BookingService.get_booking_details(session, booking_id)
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Access control logic
    if current_user:
        # Authenticated user access
        user_id = current_user["id"]
        if details.get("user_id") and details["user_id"] != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        # Guest access - require email verification
        if not guest_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Guest email is required for accessing booking details"
            )
        
        # Verify the guest email matches the booking
        if details.get("guest_email") != guest_email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return details


@router.get("/user/bookings", response_model=List[Dict[str, Any]])
async def get_user_bookings(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None),
):
    bookings = await BookingService.get_user_bookings(
        session=session,
        user_id=current_user["id"],
        limit=limit,
        offset=offset,
        status=status,
    )
    return bookings


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    guest_email: Optional[str] = Query(None, description="Guest email for verification")
):
    # Verify access before cancelling
    booking_details = await BookingService.get_booking_details(session, booking_id)
    if not booking_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    # Access control
    if current_user:
        user_id = current_user["id"]
        if booking_details.get("user_id") and booking_details["user_id"] != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        # Guest access - require email verification
        if not guest_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest email is required for cancelling bookings"
            )
        if booking_details.get("guest_email") != guest_email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    success = await BookingService.cancel_booking(
        session=session, booking_id=booking_id, user_id=(current_user["id"] if current_user else None)
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking cannot be cancelled")

    AuditService.log_action(
        action="booking_cancelled",
        entity_type="booking",
        entity_id=booking_id,
        actor_id=(current_user["id"] if current_user else None),
        actor_role=(current_user["role"] if current_user else "guest"),
        metadata={"guest_email": guest_email} if guest_email else {},
    )
    return {"message": "Booking cancelled successfully"}


@router.get("/reference/{booking_reference}", response_model=Dict[str, Any])
async def get_booking_by_reference(
    booking_reference: str, 
    session: AsyncSession = Depends(get_db),
    guest_email: Optional[str] = Query(None, description="Guest email for verification")
):
    details = await BookingService.get_booking_by_reference(session, booking_reference)
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    # For guest bookings, verify email matches
    if details.get("guest_email") and guest_email:
        if details.get("guest_email") != guest_email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return details


@router.get("/guest/{email}", response_model=List[Dict[str, Any]])
async def get_guest_bookings(
    email: EmailStr,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None)
):
    """Get all bookings for a guest email address."""
    bookings = await BookingService.get_guest_bookings(
        session=session,
        guest_email=email,
        limit=limit,
        offset=offset,
        status=status
    )
    return bookings


@router.get("/price-comparison")
async def get_price_comparison(
    origin: str = Query(...),
    destination: str = Query(...),
    date: datetime = Query(...),
    session: AsyncSession = Depends(get_db),
):
    routes = await BookingService.search_routes(
        session=session,
        origin=origin,
        destination=destination,
        date=date,
        filters={},
    )

    comparison_summary = TransportProviderService.get_price_comparison_summary(routes)

    provider_comparison: Dict[str, Any] = {}
    for route in routes:
        code = route["provider_code"]
        data = provider_comparison.setdefault(
            code,
            {
                "provider_name": route["provider_name"],
                "routes": [],
                "price_range": {"min": float("inf"), "max": 0},
                "duration_range": {"min": float("inf"), "max": 0},
                "total_options": 0,
            },
        )
        data["routes"].append(route)
        data["total_options"] += 1
        price = route["base_price"]
        duration = route["duration_minutes"]
        data["price_range"]["min"] = min(data["price_range"]["min"], price)
        data["price_range"]["max"] = max(data["price_range"]["max"], price)
        data["duration_range"]["min"] = min(data["duration_range"]["min"], duration)
        data["duration_range"]["max"] = max(data["duration_range"]["max"], duration)

    for code, data in provider_comparison.items():
        prices = [r["base_price"] for r in data["routes"]]
        durations = [r["duration_minutes"] for r in data["routes"]]
        data["price_range"]["average"] = sum(prices) / len(prices) if prices else 0
        data["duration_range"]["average"] = sum(durations) / len(durations) if durations else 0

    return {
        "comparison_summary": comparison_summary,
        "provider_comparison": provider_comparison,
        "cheapest_option": min(routes, key=lambda x: x["base_price"]) if routes else None,
        "fastest_option": min(routes, key=lambda x: x["duration_minutes"]) if routes else None,
        "search_criteria": {"origin": origin, "destination": destination, "date": date.isoformat()},
    }


@router.get("/providers", response_model=List[Dict[str, Any]])
async def get_all_providers(session: AsyncSession = Depends(get_db)):
    """Get all active transport providers."""
    providers = await TransportProviderService.get_all_providers(session)
    return [
        {
            "id": str(provider.id),
            "name": provider.name,
            "code": provider.code,
            "transport_type": provider.transport_type.value,
            "contact_email": provider.contact_email,
            "contact_phone": provider.contact_phone,
            "website_url": provider.website_url,
            "is_active": provider.is_active,
            "created_at": provider.created_at.isoformat(),
            "updated_at": provider.updated_at.isoformat()
        }
        for provider in providers
    ]


@router.get("/providers/statistics", response_model=Dict[str, Any])
async def get_provider_statistics(session: AsyncSession = Depends(get_db)):
    stats = await TransportProviderService.get_route_statistics(session)
    return stats


@router.get("/statistics", response_model=Dict[str, Any])
async def get_booking_statistics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    stats = await BookingService.get_booking_statistics(session)
    return stats


# ---- Admin-only ----
async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.get("/admin/all", response_model=List[Dict[str, Any]])
async def admin_get_all_bookings(
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[BookingStatus] = Query(None),
):
    bookings = await BookingService.get_all_bookings(
        session=session, limit=limit, offset=offset, status=status
    )
    return bookings


@router.post("/admin/{booking_id}/confirm")
async def admin_confirm_booking(
    booking_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    success = await BookingService.confirm_booking(session, booking_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking not found or cannot be confirmed")

    AuditService.log_action(
        action="booking_confirmed",
        entity_type="booking",
        entity_id=booking_id,
        actor_id=current_admin["id"],
        actor_role=current_admin["role"],
        metadata={},
    )
    return {"message": "Booking confirmed successfully"}
