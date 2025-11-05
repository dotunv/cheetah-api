#!/usr/bin/env python3
"""
Database seeding script for Cheetah API.
Creates comprehensive transport provider data with routes and schedules.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import database components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import AsyncSessionLocal
from app.database.models import TransportProvider, Route, Schedule, TransportType
from app.services.mock_transport_data import MockTransportData


async def create_transport_providers(session: AsyncSession) -> Dict[str, TransportProvider]:
    """Create transport providers from mock data."""
    providers = {}
    new_provider_count = 0
    existing_provider_count = 0
    
    for key, data in MockTransportData.TRANSPORT_PROVIDERS.items():
        provider_code = data["code"]  # Use the actual code from data
        
        # Check if provider already exists
        existing_result = await session.execute(
            select(TransportProvider).where(TransportProvider.code == provider_code)
        )
        existing_provider = existing_result.scalar_one_or_none()
        
        if existing_provider:
            print(f"  ⚠️  Provider {provider_code} already exists, skipping...")
            providers[key] = existing_provider  # Add existing provider to dict
            existing_provider_count += 1
            continue
        
        provider = TransportProvider(
            name=data["name"],
            code=provider_code,
            transport_type=TransportType.BUS,
            contact_email=data.get("email"),
            contact_phone=data.get("phone"),
            website_url=data.get("website"),
            is_active=True
        )
        
        session.add(provider)
        await session.flush()  # Get the ID
        providers[key] = provider  # Use the dictionary key to lookup
        new_provider_count += 1
        
        print(f"  ✅ Added provider: {data['name']} ({provider_code})")
    
    print(f"  ✅ Created {new_provider_count} providers, {existing_provider_count} already existed")
    return providers


async def create_routes(session: AsyncSession, providers: Dict[str, TransportProvider]) -> List[Route]:
    """Create routes for all providers."""
    routes = []
    new_route_count = 0
    existing_route_count = 0
    
    for code, provider_data in MockTransportData.TRANSPORT_PROVIDERS.items():
        provider = providers.get(code)
        if not provider:
            continue
            
        print(f"  📍 Creating routes for {provider_data['name']}...")
        
        for route_data in provider_data["routes"]:
            origin = route_data["origin"]
            destination = route_data["destination"]
            duration_hours = route_data["duration_hours"]
            
            # Generate route code
            route_code = f"{code.upper()}_{origin[:3].upper()}_{destination[:3].upper()}"
            
            # Get distance from matrix
            distance = _get_distance(origin, destination)
            
            # Check if route already exists
            existing_result = await session.execute(
                select(Route).where(
                    Route.provider_id == provider.id,
                    Route.origin == origin,
                    Route.destination == destination
                )
            )
            existing_route = existing_result.scalar_one_or_none()
            if existing_route:
                routes.append(existing_route)  # Add existing route for schedule creation
                existing_route_count += 1
                continue
            
            route = Route(
                provider_id=provider.id,
                origin=origin,
                destination=destination,
                route_code=route_code,
                distance_km=distance,
                estimated_duration_hours=duration_hours,
                is_active=True
            )
            
            session.add(route)
            await session.flush()
            routes.append(route)
            new_route_count += 1
    
    print(f"  ✅ Created {new_route_count} routes, {existing_route_count} already existed")
    return routes


async def create_schedules(session: AsyncSession, routes: List[Route]):
    """Create schedules for all routes."""
    new_schedule_count = 0
    existing_schedule_count = 0
    
    # Generate schedules for the next 30 days
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Create lookup map from provider code to mock data key
    code_to_key_map = {}
    for key, data in MockTransportData.TRANSPORT_PROVIDERS.items():
        code_to_key_map[data["code"]] = key

    # Use no_autoflush to prevent premature flushes during bulk schedule creation
    # This addresses the "ConnectionDoesNotExistError" by allowing explicit commits.
    with session.no_autoflush:
        for route in routes:
            provider_code = await _get_provider_code_by_id(session, route.provider_id)
            # Get the dictionary key for this provider code
            provider_key = code_to_key_map.get(provider_code)
            if not provider_key:
                continue
            provider_data = MockTransportData.TRANSPORT_PROVIDERS.get(provider_key, {})
            
            # Find route data from provider
            route_data = None
            for rd in provider_data.get("routes", []):
                if (rd["origin"] == route.origin and rd["destination"] == route.destination):
                    route_data = rd
                    break
            
            if not route_data:
                continue
            
            frequency = route_data.get("frequency", "daily")
            duration_hours = route_data["duration_hours"]
            
            print(f"  ⏰ Creating schedules for {route.origin} → {route.destination} ({provider_code})...")
            
            # Generate schedules for next 30 days
            for day_offset in range(30):
                current_date = start_date + timedelta(days=day_offset)
                
                # Get departure times based on frequency
                departure_times = _get_departure_times(frequency, current_date)
                
                for time_idx, departure_time in enumerate(departure_times):
                    # Skip some schedules randomly for realism (5% chance)
                    if random.random() < 0.05:
                        continue
                    
                    arrival_time = departure_time + timedelta(hours=duration_hours)
                    duration_minutes = int(duration_hours * 60)
                    
                    # Generate schedule code
                    schedule_code = f"{provider_code.upper()}_{current_date.strftime('%Y%m%d')}_{time_idx:02d}"
                    
                    # Choose vehicle type based on provider specialties
                    vehicle_types = provider_data.get("specialties", ["AC Bus"])
                    vehicle_type = random.choice(vehicle_types)
                    
                    # Get vehicle specifications
                    vehicle_specs = MockTransportData.VEHICLE_TYPES.get(vehicle_type, MockTransportData.VEHICLE_TYPES["AC Bus"])
                    total_seats = vehicle_specs["capacity"]
                    
                    # Generate realistic seat availability (60-95% occupancy)
                    occupancy_rate = random.uniform(0.6, 0.95)
                    available_seats = max(1, int(total_seats * (1 - occupancy_rate)))
                    
                    # Calculate base price
                    base_price = MockTransportData.calculate_base_price(
                        route.origin, route.destination, vehicle_type
                    )
                    
                    # Apply time-based pricing
                    base_price = MockTransportData.apply_time_multiplier(base_price, departure_time)
                    
                    # Apply day-of-week pricing
                    base_price = MockTransportData.apply_day_multiplier(base_price, departure_time)
                    
                    # Add some random variation (±5%)
                    price_variation = random.uniform(0.95, 1.05)
                    base_price *= price_variation
                    base_price = round(base_price, 2)
                    
                    # Get amenities for vehicle type
                    amenities = MockTransportData.get_vehicle_amenities(vehicle_type)
                    amenities_json = json.dumps(amenities)
                    
                    # Check if schedule already exists
                    existing_result = await session.execute(
                        select(Schedule).where(
                            Schedule.route_id == route.id,
                            Schedule.schedule_code == schedule_code
                        )
                    )
                    if existing_result.scalar_one_or_none():
                        existing_schedule_count += 1
                        continue
                    
                    schedule = Schedule(
                        provider_id=route.provider_id,
                        route_id=route.id,
                        schedule_code=schedule_code,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        duration_minutes=duration_minutes,
                        total_seats=total_seats,
                        available_seats=available_seats,
                        base_price=base_price,
                        vehicle_type=vehicle_type,
                        amenities=amenities_json,
                        is_active=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    session.add(schedule)
                    new_schedule_count += 1
                    
                    # Commit in batches to avoid memory issues
                    if new_schedule_count % 1000 == 0:
                        await session.commit()
                        print(f"    📊 Created {new_schedule_count} schedules so far...")
    
    print(f"  ✅ Created {new_schedule_count} schedules, {existing_schedule_count} already existed")


def _get_distance(origin: str, destination: str) -> float:
    """Get distance between two cities."""
    distance = MockTransportData.DISTANCE_MATRIX.get((origin, destination))
    if distance is None:
        distance = MockTransportData.DISTANCE_MATRIX.get((destination, origin))
    if distance is None:
        # Estimate based on coordinates if not in matrix
        return 500.0
    return float(distance)


async def _get_provider_code_by_id(session: AsyncSession, provider_id) -> str:
    """Get provider code by provider ID."""
    result = await session.execute(
        select(TransportProvider.code).where(TransportProvider.id == provider_id)
    )
    code = result.scalar_one_or_none()
    return code if code else "unknown"


def _get_departure_times(frequency: str, date: datetime) -> List[datetime]:
    """Get departure times based on frequency."""
    base_times = []
    
    if frequency == "every_30_minutes":
        base_times = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in [0, 30]]
    elif frequency == "every_hour":
        base_times = [f"{h:02d}:00" for h in range(6, 22)]
    elif frequency == "every_2_hours":
        base_times = [f"{h:02d}:00" for h in range(6, 22, 2)]
    elif frequency == "every_3_hours":
        base_times = [f"{h:02d}:00" for h in range(6, 21, 3)]
    else:  # daily
        base_times = ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
    
    # Filter out some schedules randomly for realism (10% chance)
    base_times = [time for time in base_times if random.random() > 0.1]
    
    departure_times = []
    for base_time in base_times:
        departure_time = datetime.combine(date.date(), datetime.strptime(base_time, "%H:%M").time())
        departure_times.append(departure_time)
    
    return departure_times


async def print_seed_summary(session: AsyncSession):
    """Print a summary of seeded data."""
    from sqlalchemy import func
    
    print("\n" + "="*60)
    print("📊 SEED DATA SUMMARY")
    print("="*60)
    
    # Count providers
    providers_result = await session.execute(select(func.count(TransportProvider.id)))
    provider_count = providers_result.scalar()
    print(f"🚌 Transport Providers: {provider_count}")
    
    # Count routes
    routes_result = await session.execute(select(func.count(Route.id)))
    route_count = routes_result.scalar()
    print(f"🛣️  Routes: {route_count}")
    
    # Count schedules
    schedules_result = await session.execute(select(func.count(Schedule.id)))
    schedule_count = schedules_result.scalar()
    print(f"⏰ Schedules: {schedule_count}")
    
    # Count active schedules
    active_schedules_result = await session.execute(
        select(func.count(Schedule.id)).where(Schedule.is_active == True)
    )
    active_schedule_count = active_schedules_result.scalar()
    print(f"✅ Active Schedules: {active_schedule_count}")
    
    # Average price
    price_result = await session.execute(
        select(func.avg(Schedule.base_price)).where(Schedule.is_active == True)
    )
    avg_price = price_result.scalar()
    print(f"💰 Average Price: ₦{avg_price:.2f}")
    
    # Provider breakdown
    print("\n🚌 PROVIDER BREAKDOWN:")
    providers_result = await session.execute(
        select(
            TransportProvider.name,
            TransportProvider.code,
            func.count(Route.id.distinct()).label('route_count'),
            func.count(Schedule.id).label('schedule_count')
        )
        .select_from(TransportProvider)
        .outerjoin(Route, TransportProvider.id == Route.provider_id)
        .outerjoin(Schedule, Route.id == Schedule.route_id)
        .group_by(TransportProvider.id, TransportProvider.name, TransportProvider.code)
        .order_by(func.count(Route.id.distinct()).desc())
    )
    
    for row in providers_result:
        print(f"  • {row.name} ({row.code}): {row.route_count} routes, {row.schedule_count} schedules")
    
    # Top routes by schedule count
    print("\n🛣️  TOP ROUTES BY SCHEDULE COUNT:")
    routes_result = await session.execute(
        select(
            Route.origin,
            Route.destination,
            func.count(Schedule.id).label('schedule_count')
        )
        .select_from(Route)
        .outerjoin(Schedule, (Route.id == Schedule.route_id) & (Schedule.is_active == True))
        .group_by(Route.id, Route.origin, Route.destination)
        .order_by(func.count(Schedule.id).desc())
        .limit(10)
    )
    
    for row in routes_result:
        print(f"  • {row.origin} → {row.destination}: {row.schedule_count} schedules")
    
    print("\n🎉 Seed data creation completed successfully!")
    print("The database is now ready for the frontend application.")


async def main():
    """Main seeding function."""
    print("🌱 Starting database seeding...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Seed transport providers
            print("\n📦 Seeding transport providers...")
            providers = await create_transport_providers(session)
            
            # Step 2: Seed routes
            print("\n🛣️  Seeding routes...")
            routes = await create_routes(session, providers)
            
            # Step 3: Seed schedules
            print("\n⏰ Seeding schedules...")
            await create_schedules(session, routes)
            
            # Commit all changes
            await session.commit()
            print("\n✅ All data seeded successfully!")
            
            # Print summary
            await print_seed_summary(session)
            
            print("\n🚀 Next steps:")
            print("1. Start the API server: uv run uvicorn app.main:app --reload")
            print("2. The frontend can now search for routes and schedules")
            print("3. Users can create bookings through the frontend")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
