#!/usr/bin/env python3
"""
Verify the seeded database data.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import AsyncSessionLocal
from app.database.models import (
    User, TransportProvider, Route, Schedule, Booking,
    InsurancePolicy, WifiCode, UserRole, BookingStatus
)

async def verify_data():
    """Verify the seeded data."""
    print("🔍 Verifying database data...")
    
    async with AsyncSessionLocal() as session:
        # Count users by role
        user_counts = await session.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        print("\n👥 Users by role:")
        for role, count in user_counts:
            print(f"   • {role.value.title()}: {count}")
        
        # Count transport providers
        provider_count = await session.execute(select(func.count(TransportProvider.id)))
        print(f"\n🚌 Transport Providers: {provider_count.scalar()}")
        
        # Count routes by provider
        route_counts = await session.execute(
            select(TransportProvider.name, func.count(Route.id))
            .join(Route)
            .group_by(TransportProvider.name)
        )
        print("\n🛣️ Routes by provider:")
        for provider_name, count in route_counts:
            print(f"   • {provider_name}: {count}")
        
        # Count schedules
        schedule_count = await session.execute(select(func.count(Schedule.id)))
        print(f"\n📅 Total Schedules: {schedule_count.scalar()}")
        
        # Count bookings by status
        booking_counts = await session.execute(
            select(Booking.booking_status, func.count(Booking.id))
            .group_by(Booking.booking_status)
        )
        print("\n🎫 Bookings by status:")
        for status, count in booking_counts:
            print(f"   • {status.value.title()}: {count}")
        
        # Count insurance policies
        policy_count = await session.execute(select(func.count(InsurancePolicy.id)))
        print(f"\n🛡️ Insurance Policies: {policy_count.scalar()}")
        
        # Count WiFi codes
        wifi_count = await session.execute(select(func.count(WifiCode.id)))
        print(f"\n📶 WiFi Codes: {wifi_count.scalar()}")
        
        # Sample some data
        print("\n📋 Sample Data:")
        
        # Sample routes
        sample_routes = await session.execute(
            select(Route.origin, Route.destination, Route.distance_km)
            .limit(5)
        )
        print("\n   Sample Routes:")
        for origin, destination, distance in sample_routes:
            print(f"     • {origin} → {destination} ({distance} km)")
        
        # Sample bookings
        sample_bookings = await session.execute(
            select(Booking.booking_reference, Booking.total_amount, Booking.booking_status)
            .limit(5)
        )
        print("\n   Sample Bookings:")
        for ref, amount, status in sample_bookings:
            print(f"     • {ref}: ₦{amount:,.0f} ({status.value})")
        
        print("\n✅ Data verification completed!")

if __name__ == "__main__":
    asyncio.run(verify_data())
