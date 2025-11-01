from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.database import get_db
from ..database.models import TransportProvider, Route, Schedule, TransportType
from ..services.transport_provider_service import TransportProviderService
from .auth import get_current_user

router = APIRouter()


# ---- Schemas ----
class ProviderResponse(BaseModel):
    id: str
    name: str
    code: str
    transport_type: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


class ProviderCreateRequest(BaseModel):
    name: str
    code: str
    transport_type: str = "bus"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None


class ProviderUpdateRequest(BaseModel):
    name: Optional[str] = None
    transport_type: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleCreateRequest(BaseModel):
    route_id: str
    schedule_code: str
    departure_time: datetime
    arrival_time: datetime
    total_seats: int
    base_price: float
    vehicle_type: Optional[str] = None
    amenities: Optional[List[str]] = None


class ScheduleUpdateRequest(BaseModel):
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None
    base_price: Optional[float] = None
    vehicle_type: Optional[str] = None
    amenities: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookRequest(BaseModel):
    schedule_id: str
    available_seats: int
    price_update: Optional[float] = None
    status: Optional[str] = None


# ---- Public Endpoints ----
@router.get("/", response_model=List[ProviderResponse])
async def get_all_providers(
    session: AsyncSession = Depends(get_db),
    active_only: bool = Query(True)
):
    """Get all transport providers."""
    providers = await TransportProviderService.get_all_providers(session)
    
    if active_only:
        providers = [p for p in providers if p.is_active]
    
    return [
        ProviderResponse(
            id=str(provider.id),
            name=provider.name,
            code=provider.code,
            transport_type=provider.transport_type.value,
            contact_email=provider.contact_email,
            contact_phone=provider.contact_phone,
            website_url=provider.website_url,
            is_active=provider.is_active,
            created_at=provider.created_at.isoformat(),
            updated_at=provider.updated_at.isoformat()
        )
        for provider in providers
    ]


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get single transport provider details."""
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        code=provider.code,
        transport_type=provider.transport_type.value,
        contact_email=provider.contact_email,
        contact_phone=provider.contact_phone,
        website_url=provider.website_url,
        is_active=provider.is_active,
        created_at=provider.created_at.isoformat(),
        updated_at=provider.updated_at.isoformat()
    )


@router.get("/code/{provider_code}", response_model=ProviderResponse)
async def get_provider_by_code(
    provider_code: str,
    session: AsyncSession = Depends(get_db)
):
    """Get transport provider by code."""
    provider = await TransportProviderService.get_provider_by_code(session, provider_code)
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        code=provider.code,
        transport_type=provider.transport_type.value,
        contact_email=provider.contact_email,
        contact_phone=provider.contact_phone,
        website_url=provider.website_url,
        is_active=provider.is_active,
        created_at=provider.created_at.isoformat(),
        updated_at=provider.updated_at.isoformat()
    )


# ---- Admin/Provider Management Endpoints ----
@router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreateRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new transport provider (admin only)."""
    if current_user["role"] not in ["admin", "provider"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or provider access required"
        )
    
    # Validate transport type
    try:
        transport_type = TransportType(provider_data.transport_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transport type. Must be 'bus', 'train', or 'ferry'"
        )
    
    provider = await TransportProviderService.create_or_update_provider(
        session=session,
        name=provider_data.name,
        code=provider_data.code,
        transport_type=transport_type,
        contact_email=provider_data.contact_email,
        contact_phone=provider_data.contact_phone,
        website_url=provider_data.website_url,
        api_endpoint=provider_data.api_endpoint,
        api_key=provider_data.api_key
    )
    
    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        code=provider.code,
        transport_type=provider.transport_type.value,
        contact_email=provider.contact_email,
        contact_phone=provider.contact_phone,
        website_url=provider.website_url,
        is_active=provider.is_active,
        created_at=provider.created_at.isoformat(),
        updated_at=provider.updated_at.isoformat()
    )


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    provider_data: ProviderUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update transport provider (admin/provider only)."""
    if current_user["role"] not in ["admin", "provider"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or provider access required"
        )
    
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    # Update fields
    if provider_data.name is not None:
        provider.name = provider_data.name
    if provider_data.transport_type is not None:
        try:
            provider.transport_type = TransportType(provider_data.transport_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transport type"
            )
    if provider_data.contact_email is not None:
        provider.contact_email = provider_data.contact_email
    if provider_data.contact_phone is not None:
        provider.contact_phone = provider_data.contact_phone
    if provider_data.website_url is not None:
        provider.website_url = provider_data.website_url
    if provider_data.api_endpoint is not None:
        provider.api_endpoint = provider_data.api_endpoint
    if provider_data.api_key is not None:
        provider.api_key = provider_data.api_key
    if provider_data.is_active is not None:
        provider.is_active = provider_data.is_active
    
    provider.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(provider)
    
    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        code=provider.code,
        transport_type=provider.transport_type.value,
        contact_email=provider.contact_email,
        contact_phone=provider.contact_phone,
        website_url=provider.website_url,
        is_active=provider.is_active,
        created_at=provider.created_at.isoformat(),
        updated_at=provider.updated_at.isoformat()
    )


@router.post("/{provider_id}/schedules/batch", status_code=status.HTTP_201_CREATED)
async def upload_schedules_batch(
    provider_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Upload schedules in batch (CSV/JSON file) (provider only)."""
    if current_user["role"] not in ["admin", "provider"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider access required"
        )
    
    # Verify provider exists
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    # Mock batch upload processing
    content = await file.read()
    
    # In a real implementation, you would parse the file and create schedules
    return {
        "message": f"Batch upload initiated for {provider.name}",
        "file_name": file.filename,
        "file_size": len(content),
        "status": "processing",
        "estimated_completion": (datetime.now(timezone.utc).timestamp() + 300)  # 5 minutes
    }


@router.put("/{provider_id}/schedules/{schedule_id}")
async def update_schedule(
    provider_id: str,
    schedule_id: str,
    schedule_data: ScheduleUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update specific schedule (provider only)."""
    if current_user["role"] not in ["admin", "provider"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider access required"
        )
    
    # Verify provider exists
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    # Mock schedule update
    return {
        "message": f"Schedule {schedule_id} updated for {provider.name}",
        "schedule_id": schedule_id,
        "updated_fields": [k for k, v in schedule_data.dict().items() if v is not None],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/{provider_id}/webhooks/schedule-update")
async def webhook_schedule_update(
    provider_id: str,
    webhook_data: WebhookRequest,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Webhook endpoint for providers to push real-time updates."""
    # Verify provider exists
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    # Mock webhook processing
    return {
        "message": f"Webhook received from {provider.name}",
        "schedule_id": webhook_data.schedule_id,
        "status": "processed",
        "received_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/{provider_id}/schedules", response_model=List[Dict[str, Any]])
async def get_provider_schedules(
    provider_id: str,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get schedules for a specific provider."""
    # Verify provider exists
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    # Get schedules for provider
    schedules_result = await session.execute(
        select(Schedule)
        .where(Schedule.provider_id == provider_id)
        .limit(limit)
        .offset(offset)
    )
    schedules = schedules_result.scalars().all()
    
    return [
        {
            "id": str(schedule.id),
            "schedule_code": schedule.schedule_code,
            "departure_time": schedule.departure_time.isoformat(),
            "arrival_time": schedule.arrival_time.isoformat(),
            "duration_minutes": schedule.duration_minutes,
            "total_seats": schedule.total_seats,
            "available_seats": schedule.available_seats,
            "base_price": schedule.base_price,
            "vehicle_type": schedule.vehicle_type,
            "amenities": schedule.amenities.split(",") if schedule.amenities else [],
            "is_active": schedule.is_active,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat()
        }
        for schedule in schedules
    ]


@router.get("/{provider_id}/statistics", response_model=Dict[str, Any])
async def get_provider_statistics(
    provider_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get statistics for a specific provider."""
    # Verify provider exists
    result = await session.execute(
        select(TransportProvider).where(TransportProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport provider not found"
        )
    
    # Mock provider statistics
    return {
        "provider_id": provider_id,
        "provider_name": provider.name,
        "total_routes": 12,
        "active_schedules": 48,
        "total_bookings": 1250,
        "revenue": 125000.0,
        "average_rating": 4.2,
        "on_time_performance": 87.5
    }
