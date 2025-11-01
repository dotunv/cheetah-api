from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database.database import get_db
from ..database.models import Booking, User, InsurancePolicy, WifiCode, TransportProvider, Schedule
from ..services.booking_service import BookingService
from ..services.insurance_service import InsuranceService
from ..services.wifi_service import WifiService
from .auth import get_current_user

router = APIRouter()


# ---- Schemas ----
class BookingTrendsResponse(BaseModel):
    period: str
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    revenue: float
    average_booking_value: float
    trends: List[Dict[str, Any]]


class UserDemographicsResponse(BaseModel):
    total_users: int
    active_users: int
    new_users: int
    user_growth_rate: float
    demographics: Dict[str, Any]


class ProviderPerformanceResponse(BaseModel):
    provider_id: str
    provider_name: str
    total_bookings: int
    revenue: float
    average_rating: float
    on_time_performance: float
    customer_satisfaction: float


class RevenueAnalyticsResponse(BaseModel):
    total_revenue: float
    revenue_growth: float
    revenue_by_provider: List[Dict[str, Any]]
    revenue_by_route: List[Dict[str, Any]]
    monthly_revenue: List[Dict[str, Any]]


class SystemStatsResponse(BaseModel):
    total_bookings: int
    total_users: int
    total_providers: int
    active_insurance_policies: int
    active_wifi_codes: int
    system_health: str


# ---- Admin Analytics Endpoints ----
@router.get("/booking-trends", response_model=BookingTrendsResponse)
async def get_booking_trends(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    provider_id: Optional[str] = Query(None),
    route: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get booking trends analytics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Build query
    query = select(Booking).where(
        and_(
            Booking.created_at >= start_date,
            Booking.created_at <= end_date
        )
    )
    
    if provider_id:
        # Join with schedules to filter by provider
        query = query.join(Schedule, Booking.schedule_id == Schedule.id)
        query = query.where(Schedule.provider_id == provider_id)
    
    result = await session.execute(query)
    bookings = result.scalars().all()
    
    # Calculate trends
    total_bookings = len(bookings)
    confirmed_bookings = len([b for b in bookings if b.booking_status.value == "confirmed"])
    cancelled_bookings = len([b for b in bookings if b.booking_status.value == "cancelled"])
    revenue = sum(b.total_amount for b in bookings if b.payment_status.value == "paid")
    average_booking_value = revenue / total_bookings if total_bookings > 0 else 0
    
    # Generate daily trends for the period
    trends = []
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        daily_bookings = [b for b in bookings if current_date <= b.created_at < next_date]
        
        trends.append({
            "date": current_date.isoformat(),
            "bookings": len(daily_bookings),
            "revenue": sum(b.total_amount for b in daily_bookings if b.payment_status.value == "paid")
        })
        current_date = next_date
    
    return BookingTrendsResponse(
        period=f"{start_date.date()} to {end_date.date()}",
        total_bookings=total_bookings,
        confirmed_bookings=confirmed_bookings,
        cancelled_bookings=cancelled_bookings,
        revenue=revenue,
        average_booking_value=average_booking_value,
        trends=trends
    )


@router.get("/user-demographics", response_model=UserDemographicsResponse)
async def get_user_demographics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user demographics analytics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Total users
    total_users_result = await session.execute(select(User))
    total_users = len(total_users_result.scalars().all())
    
    # Active users (users with bookings in last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    active_users_result = await session.execute(
        select(User).join(Booking, User.id == Booking.user_id)
        .where(Booking.created_at >= thirty_days_ago)
    )
    active_users = len(set(user.id for user in active_users_result.scalars().all()))
    
    # New users (registered in last 30 days)
    new_users_result = await session.execute(
        select(User).where(User.created_at >= thirty_days_ago)
    )
    new_users = len(new_users_result.scalars().all())
    
    # User growth rate
    previous_period_start = thirty_days_ago - timedelta(days=30)
    previous_period_users_result = await session.execute(
        select(User).where(
            and_(
                User.created_at >= previous_period_start,
                User.created_at < thirty_days_ago
            )
        )
    )
    previous_period_users = len(previous_period_users_result.scalars().all())
    user_growth_rate = ((new_users - previous_period_users) / previous_period_users * 100) if previous_period_users > 0 else 0
    
    # Mock demographics data
    demographics = {
        "age_groups": {
            "18-25": 25,
            "26-35": 40,
            "36-45": 25,
            "46-55": 8,
            "55+": 2
        },
        "gender_distribution": {
            "male": 55,
            "female": 42,
            "other": 3
        },
        "location_distribution": {
            "Lagos": 45,
            "Abuja": 20,
            "Port Harcourt": 15,
            "Kano": 10,
            "Other": 10
        },
        "booking_frequency": {
            "1-2 trips": 60,
            "3-5 trips": 25,
            "6-10 trips": 10,
            "10+ trips": 5
        }
    }
    
    return UserDemographicsResponse(
        total_users=total_users,
        active_users=active_users,
        new_users=new_users,
        user_growth_rate=user_growth_rate,
        demographics=demographics
    )


@router.get("/provider-performance", response_model=List[ProviderPerformanceResponse])
async def get_provider_performance(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get provider performance analytics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all providers
    providers_result = await session.execute(select(TransportProvider))
    providers = providers_result.scalars().all()
    
    performance_data = []
    
    for provider in providers:
        # Get bookings for this provider
        bookings_result = await session.execute(
            select(Booking).join(Schedule, Booking.schedule_id == Schedule.id)
            .where(Schedule.provider_id == provider.id)
        )
        provider_bookings = bookings_result.scalars().all()
        
        total_bookings = len(provider_bookings)
        revenue = sum(b.total_amount for b in provider_bookings if b.payment_status.value == "paid")
        
        # Mock performance metrics
        performance_data.append(ProviderPerformanceResponse(
            provider_id=str(provider.id),
            provider_name=provider.name,
            total_bookings=total_bookings,
            revenue=revenue,
            average_rating=4.0 + (total_bookings % 10) * 0.1,  # Mock rating
            on_time_performance=85.0 + (total_bookings % 15),  # Mock on-time performance
            customer_satisfaction=80.0 + (total_bookings % 20)  # Mock satisfaction
        ))
    
    return performance_data


@router.get("/revenue", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get revenue analytics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Set default date range
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get paid bookings in date range
    bookings_result = await session.execute(
        select(Booking).where(
            and_(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date,
                Booking.payment_status == "paid"
            )
        )
    )
    bookings = bookings_result.scalars().all()
    
    total_revenue = sum(b.total_amount for b in bookings)
    
    # Calculate revenue growth (compare with previous period)
    previous_start = start_date - (end_date - start_date)
    previous_bookings_result = await session.execute(
        select(Booking).where(
            and_(
                Booking.created_at >= previous_start,
                Booking.created_at < start_date,
                Booking.payment_status == "paid"
            )
        )
    )
    previous_revenue = sum(b.total_amount for b in previous_bookings_result.scalars().all())
    revenue_growth = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    
    # Revenue by provider
    revenue_by_provider = []
    providers_result = await session.execute(select(TransportProvider))
    providers = providers_result.scalars().all()
    
    for provider in providers:
        provider_bookings = [b for b in bookings if b.schedule.provider_id == provider.id]
        provider_revenue = sum(b.total_amount for b in provider_bookings)
        revenue_by_provider.append({
            "provider_name": provider.name,
            "revenue": provider_revenue,
            "percentage": (provider_revenue / total_revenue * 100) if total_revenue > 0 else 0
        })
    
    # Mock revenue by route
    revenue_by_route = [
        {"route": "Lagos - Abuja", "revenue": total_revenue * 0.4, "percentage": 40},
        {"route": "Lagos - Port Harcourt", "revenue": total_revenue * 0.3, "percentage": 30},
        {"route": "Abuja - Kano", "revenue": total_revenue * 0.2, "percentage": 20},
        {"route": "Other Routes", "revenue": total_revenue * 0.1, "percentage": 10}
    ]
    
    # Monthly revenue (mock data)
    monthly_revenue = []
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        monthly_revenue.append({
            "month": current_month.strftime("%Y-%m"),
            "revenue": total_revenue * (0.8 + (current_month.month % 3) * 0.1)
        })
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    return RevenueAnalyticsResponse(
        total_revenue=total_revenue,
        revenue_growth=revenue_growth,
        revenue_by_provider=revenue_by_provider,
        revenue_by_route=revenue_by_route,
        monthly_revenue=monthly_revenue
    )


@router.get("/system-stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get system statistics (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get booking statistics
    booking_stats = await BookingService.get_booking_statistics(session)
    
    # Get user count
    users_result = await session.execute(select(User))
    total_users = len(users_result.scalars().all())
    
    # Get provider count
    providers_result = await session.execute(select(TransportProvider))
    total_providers = len(providers_result.scalars().all())
    
    # Get insurance statistics
    insurance_stats = await InsuranceService.get_insurance_statistics(session)
    
    # Get WiFi statistics
    wifi_stats = await WifiService.get_wifi_statistics(session)
    
    # Determine system health
    system_health = "healthy"
    if booking_stats["total_bookings"] == 0:
        system_health = "no_data"
    elif booking_stats["confirmed_bookings"] / booking_stats["total_bookings"] < 0.7:
        system_health = "warning"
    
    return SystemStatsResponse(
        total_bookings=booking_stats["total_bookings"],
        total_users=total_users,
        total_providers=total_providers,
        active_insurance_policies=insurance_stats["active_policies"],
        active_wifi_codes=wifi_stats["active_codes"],
        system_health=system_health
    )


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get comprehensive admin dashboard data (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all analytics data
    booking_trends = await get_booking_trends(
    start_date=datetime.now(timezone.utc) - timedelta(days=30),
    end_date=datetime.now(timezone.utc),
        current_user=current_user,
        session=session
    )
    
    user_demographics = await get_user_demographics(
        current_user=current_user,
        session=session
    )
    
    provider_performance = await get_provider_performance(
        current_user=current_user,
        session=session
    )
    
    revenue_analytics = await get_revenue_analytics(
    start_date=datetime.now(timezone.utc) - timedelta(days=30),
    end_date=datetime.now(timezone.utc),
        current_user=current_user,
        session=session
    )
    
    system_stats = await get_system_stats(
        current_user=current_user,
        session=session
    )
    
    return {
        "booking_trends": booking_trends.dict(),
        "user_demographics": user_demographics.dict(),
        "provider_performance": [p.dict() for p in provider_performance],
        "revenue_analytics": revenue_analytics.dict(),
        "system_stats": system_stats.dict(),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
