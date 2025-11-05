from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database.database import get_db
from ..database.models import Booking, User, InsurancePolicy, WifiCode, TransportProvider, Schedule, BookingStatus, PaymentStatus
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
    
    # Aggregates via SQL
    base = (
        select(
            func.count(Booking.id),
            func.count().filter(Booking.booking_status == BookingStatus.CONFIRMED),
            func.count().filter(Booking.booking_status == BookingStatus.CANCELLED),
            func.coalesce(func.sum(Booking.total_amount).filter(Booking.payment_status == PaymentStatus.PAID), 0.0)
        )
        .where(and_(Booking.created_at >= start_date, Booking.created_at <= end_date))
    )
    if provider_id:
        base = base.select_from(Booking).join(Schedule, Booking.schedule_id == Schedule.id).where(Schedule.provider_id == provider_id)
    total_bookings, confirmed_bookings, cancelled_bookings, revenue = (await session.execute(base)).one()
    average_booking_value = (revenue / total_bookings) if total_bookings else 0
    
    # Generate daily trends for the period
    trends_rows = await session.execute(
        select(
            func.date_trunc('day', Booking.created_at).label('day'),
            func.count(Booking.id).label('bookings'),
            func.coalesce(func.sum(Booking.total_amount).filter(Booking.payment_status == PaymentStatus.PAID), 0.0).label('revenue'),
        )
        .where(and_(Booking.created_at >= start_date, Booking.created_at <= end_date))
        .group_by('day')
        .order_by('day')
    )
    trends = [{"date": row.day.isoformat(), "bookings": row.bookings, "revenue": float(row.revenue)} for row in trends_rows]
    
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
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    
    # Active users (users with bookings in last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    active_users = (
        await session.execute(
            select(func.count(func.distinct(User.id)))
            .join(Booking, User.id == Booking.user_id)
            .where(Booking.created_at >= thirty_days_ago)
        )
    ).scalar_one()
    
    # New users (registered in last 30 days)
    new_users = (
        await session.execute(select(func.count(User.id)).where(User.created_at >= thirty_days_ago))
    ).scalar_one()
    
    # User growth rate
    previous_period_start = thirty_days_ago - timedelta(days=30)
    previous_period_users = (
        await session.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= previous_period_start, User.created_at < thirty_days_ago)
            )
        )
    ).scalar_one()
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
    bookings_paid = await session.execute(
        select(
            func.coalesce(func.sum(Booking.total_amount), 0.0)
        ).where(and_(
            Booking.created_at >= start_date,
            Booking.created_at <= end_date,
            Booking.payment_status == "paid"
        ))
    )
    total_revenue = float(bookings_paid.scalar_one())
    
    # Calculate revenue growth (compare with previous period)
    previous_start = start_date - (end_date - start_date)
    previous_revenue = float((
        await session.execute(
            select(func.coalesce(func.sum(Booking.total_amount), 0.0)).where(
                and_(
                    Booking.created_at >= previous_start,
                    Booking.created_at < start_date,
                    Booking.payment_status == "paid"
                )
            )
        )
    ).scalar_one())
    revenue_growth = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    
    # Revenue by provider (SQL aggregate)
    provider_rows = await session.execute(
        select(
            TransportProvider.name,
            func.coalesce(func.sum(Booking.total_amount), 0.0).label("revenue")
        )
        .select_from(Booking)
        .join(Schedule, Booking.schedule_id == Schedule.id)
        .join(TransportProvider, Schedule.provider_id == TransportProvider.id)
        .where(and_(
            Booking.created_at >= start_date,
            Booking.created_at <= end_date,
            Booking.payment_status == "paid"
        ))
        .group_by(TransportProvider.name)
    )
    provider_rows = provider_rows.all()
    revenue_by_provider = [
        {
            "provider_name": name,
            "revenue": float(revenue),
            "percentage": (float(revenue) / total_revenue * 100) if total_revenue > 0 else 0
        }
        for name, revenue in provider_rows
    ]
    
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
