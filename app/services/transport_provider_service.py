import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
import random

from ..database.models import TransportProvider, Route, Schedule, TransportType
from ..database.config import get_settings
from .mock_transport_data import MockTransportData


class TransportProviderService:
    """Service for managing transport provider integrations and data."""
    
    # Use comprehensive mock data
    MOCK_PROVIDERS = MockTransportData.TRANSPORT_PROVIDERS
    
    @staticmethod
    async def search_routes(
        session: AsyncSession,
        origin: str,
        destination: str,
        date: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for routes across all enabled providers."""
        enabled_providers = get_settings().ENABLED_PROVIDERS.split(",")
        
        # Get schedules from all providers concurrently
        tasks: List[asyncio.Task] = []
        for provider_code in enabled_providers:
            provider_code = provider_code.strip()
            if provider_code:
                tasks.append(
                    TransportProviderService.mock_get_schedules(
                        provider_code, origin, destination, date
                    )
                )
        
        # Execute all provider API calls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and normalize results
        all_schedules: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, list):
                all_schedules.extend(result)
        
        # Apply filters if provided
        if filters:
            all_schedules = TransportProviderService.apply_filters(all_schedules, filters)
        
        # Apply sorting based on filters or default to departure time
        sort_by = filters.get("sort_by", "departure_time") if filters else "departure_time"
        all_schedules = TransportProviderService.apply_sorting(all_schedules, sort_by)
        
        return all_schedules

    @staticmethod
    async def get_route_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Get statistics about routes and providers."""
        # Count total routes
        routes_result = await session.execute(select(Route))
        total_routes = len(routes_result.scalars().all())
        
        # Count active schedules
        schedules_result = await session.execute(
            select(Schedule).where(Schedule.is_active == True)
        )
        active_schedules = len(schedules_result.scalars().all())
        
        # Count active providers
        providers_result = await session.execute(
            select(TransportProvider).where(TransportProvider.is_active == True)
        )
        active_providers = len(providers_result.scalars().all())
        
        return {
            "total_routes": total_routes,
            "active_schedules": active_schedules,
            "active_providers": active_providers,
            "enabled_providers": get_settings().ENABLED_PROVIDERS.split(",")
        }
    
    @staticmethod
    async def get_all_providers(session: AsyncSession) -> List[TransportProvider]:
        """Get all active transport providers."""
        result = await session.execute(
            select(TransportProvider).where(TransportProvider.is_active == True)
        )
        return result.scalars().all()

    @staticmethod
    async def get_provider_by_code(session: AsyncSession, code: str) -> Optional[TransportProvider]:
        """Get transport provider by code."""
        result = await session.execute(
            select(TransportProvider).where(TransportProvider.code == code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update_provider(
        session: AsyncSession,
        name: str,
        code: str,
        transport_type: TransportType = TransportType.BUS,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        website_url: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> TransportProvider:
        """Create or update a transport provider."""
        existing_provider = await TransportProviderService.get_provider_by_code(session, code)

        if existing_provider:
            # Update existing provider
            existing_provider.name = name
            existing_provider.transport_type = transport_type
            existing_provider.contact_email = contact_email
            existing_provider.contact_phone = contact_phone
            existing_provider.website_url = website_url
            existing_provider.api_endpoint = api_endpoint
            existing_provider.api_key = api_key
            existing_provider.updated_at = datetime.now(timezone.utc)()

            await session.commit()
            await session.refresh(existing_provider)
            return existing_provider
        else:
            # Create new provider
            provider = TransportProvider(
                name=name,
                code=code,
                transport_type=transport_type,
                contact_email=contact_email,
                contact_phone=contact_phone,
                website_url=website_url,
                api_endpoint=api_endpoint,
                api_key=api_key,
                is_active=True
            )

            session.add(provider)
            await session.commit()
            await session.refresh(provider)
            return provider

    @staticmethod
    async def mock_get_schedules(
        provider_code: str,
        origin: str,
        destination: str,
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Mock API call to get schedules from a transport provider."""
        provider_data = TransportProviderService.MOCK_PROVIDERS.get(provider_code)
        if not provider_data:
            return []

        # Check if route is available
        if not MockTransportData.is_route_available(provider_code, origin, destination):
            return []

        # Find matching route
        matching_route = None
        for route in provider_data["routes"]:
            if (route["origin"].lower() == origin.lower() and 
                route["destination"].lower() == destination.lower()):
                matching_route = route
                break

        if not matching_route:
            return []

        # Get frequency and generate schedules accordingly
        frequency = matching_route.get("frequency", "daily")
        duration_hours = matching_route["duration_hours"]
        
        # Generate schedules based on frequency
        schedules = []
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

        for i, base_time in enumerate(base_times):
            departure_time = datetime.combine(date.date(), datetime.strptime(base_time, "%H:%M").time())
            arrival_time = departure_time + timedelta(hours=duration_hours)

            # Get realistic pricing
            distance = MockTransportData.get_distance(origin, destination)
            
            # Choose vehicle type based on provider specialties
            vehicle_types = provider_data.get("specialties", ["AC Bus"])
            vehicle_type = random.choice(vehicle_types)
            
            # Calculate base price using realistic pricing
            base_price = MockTransportData.calculate_base_price(origin, destination, vehicle_type)
            
            # Apply time-based pricing
            base_price = MockTransportData.apply_time_multiplier(base_price, departure_time)
            
            # Apply day-of-week pricing
            base_price = MockTransportData.apply_day_multiplier(base_price, departure_time)
            
            # Add some random variation (±10%)
            price_variation = random.uniform(0.9, 1.1)
            base_price *= price_variation

            # Get vehicle specifications
            vehicle_specs = MockTransportData.VEHICLE_TYPES.get(vehicle_type, MockTransportData.VEHICLE_TYPES["AC Bus"])
            total_seats = vehicle_specs["capacity"]
            
            # Generate realistic seat availability (60-95% occupancy)
            occupancy_rate = random.uniform(0.6, 0.95)
            available_seats = max(1, int(total_seats * (1 - occupancy_rate)))

            # Get amenities for vehicle type
            amenities = MockTransportData.get_vehicle_amenities(vehicle_type)

            schedule = {
                "schedule_id": f"{provider_code}_{date.strftime('%Y%m%d')}_{i}",
                "provider_code": provider_code,
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time.isoformat(),
                "arrival_time": arrival_time.isoformat(),
                "duration_minutes": duration_hours * 60,
                "total_seats": total_seats,
                "available_seats": available_seats,
                "base_price": round(base_price, 2),
                "vehicle_type": vehicle_type,
                "amenities": amenities,
                "provider_name": provider_data["name"],
                "provider_phone": provider_data.get("phone", ""),
                "provider_email": provider_data.get("email", ""),
                "provider_website": provider_data.get("website", ""),
                "safety_rating": provider_data.get("safety_rating", 4.0),
                "reputation": provider_data.get("reputation", "Good"),
                "fleet_size": provider_data.get("fleet_size", 50),
                "distance_km": distance,
                "terminal_origin": random.choice(MockTransportData.CITIES.get(origin, {}).get("terminals", ["Main Terminal"])),
                "terminal_destination": random.choice(MockTransportData.CITIES.get(destination, {}).get("terminals", ["Main Terminal"])),
                "booking_policies": MockTransportData.BOOKING_POLICIES,
                "terminal_facilities": list(MockTransportData.TERMINAL_FACILITIES.keys())[:5],  # Random 5 facilities
                "safety_features": list(MockTransportData.SAFETY_STANDARDS.keys())[:5]  # Random 5 safety features
            }

            schedules.append(schedule)

        return schedules

    @staticmethod
    async def mock_get_pricing(
        provider_code: str,
        schedule_id: str,
        seats: int = 1
    ) -> Dict[str, Any]:
        """Mock API call to get pricing for a specific schedule."""
        # Extract origin and destination from schedule_id if possible
        # For now, use a default calculation
        base_price = 5000 + random.randint(1000, 3000)
        
        # Apply realistic pricing based on provider
        provider_data = TransportProviderService.MOCK_PROVIDERS.get(provider_code, {})
        if provider_data:
            # Higher-end providers charge more
            reputation_multiplier = {
                "Excellent": 1.2,
                "Very Good": 1.1,
                "Good": 1.0
            }.get(provider_data.get("reputation", "Good"), 1.0)
            base_price *= reputation_multiplier
        
        total_price = base_price * seats
        booking_fee = 200
        insurance_fee = 0  # Free insurance
        wifi_fee = 0  # Free WiFi
        
        # Add some additional fees based on provider
        convenience_fee = 100 if provider_data.get("reputation") == "Excellent" else 50
        service_fee = 150 if provider_data.get("fleet_size", 0) > 200 else 100
        
        total_fees = booking_fee + insurance_fee + wifi_fee + convenience_fee + service_fee

        return {
            "schedule_id": schedule_id,
            "provider_code": provider_code,
            "base_price_per_seat": round(base_price, 2),
            "seats_requested": seats,
            "total_price": round(total_price, 2),
            "booking_fee": booking_fee,
            "insurance_fee": insurance_fee,
            "wifi_fee": wifi_fee,
            "convenience_fee": convenience_fee,
            "service_fee": service_fee,
            "total_fees": total_fees,
            "grand_total": round(total_price + total_fees, 2),
            "currency": "NGN",
            "pricing_breakdown": {
                "base_fare": round(total_price, 2),
                "fees": total_fees,
                "discounts": 0,
                "taxes": 0
            }
        }

    @staticmethod
    async def mock_book_ticket(
        provider_code: str,
        schedule_id: str,
        passenger_details: List[Dict[str, str]],
        contact_email: str,
        contact_phone: str
    ) -> Dict[str, Any]:
        """Mock API call to book a ticket with a transport provider."""
        # Simulate API delay
        await asyncio.sleep(1)
        
        # Generate booking reference
        booking_ref = f"{provider_code.upper()}{str(uuid.uuid4())[:8]}"
        
        return {
            "success": True,
            "booking_reference": booking_ref,
            "provider_booking_reference": f"{provider_code.upper()}-{str(uuid.uuid4())[:8]}",
            "status": "CONFIRMED",
            "message": "Booking successful",
            "details": {
                "passenger_count": len(passenger_details),
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "booking_time": datetime.now(timezone.utc)().isoformat()
            }
        }

    @staticmethod
    def apply_filters(
        schedules: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to schedules."""
        filtered = schedules
        
        if "max_price" in filters:
            filtered = [s for s in filtered if s["base_price"] <= filters["max_price"]]
            
        if "min_price" in filters:
            filtered = [s for s in filtered if s["base_price"] >= filters["min_price"]]
            
        if "min_seats" in filters:
            filtered = [s for s in filtered if s["available_seats"] >= filters["min_seats"]]
            
        if "vehicle_type" in filters:
            filtered = [s for s in filtered if filters["vehicle_type"] in s["vehicle_type"]]
            
        if "vehicle_types" in filters:
            vehicle_types = set(filters["vehicle_types"])
            filtered = [s for s in filtered if any(vt in s["vehicle_type"] for vt in vehicle_types)]
            
        if "amenities" in filters:
            amenities = set(filters["amenities"])
            filtered = [s for s in filtered if amenities.issubset(set(s["amenities"]))]
            
        if "providers" in filters:
            provider_codes = set(filters["providers"])
            filtered = [s for s in filtered if s["provider_code"] in provider_codes]
            
        if "departure_after" in filters:
            departure_after = datetime.fromisoformat(filters["departure_after"])
            filtered = [s for s in filtered if datetime.fromisoformat(s["departure_time"]) >= departure_after]
            
        if "departure_before" in filters:
            departure_before = datetime.fromisoformat(filters["departure_before"])
            filtered = [s for s in filtered if datetime.fromisoformat(s["departure_time"]) <= departure_before]
            
        return filtered

    @staticmethod
    def apply_sorting(
        schedules: List[Dict[str, Any]],
        sort_by: str
    ) -> List[Dict[str, Any]]:
        """Apply sorting to schedules."""
        if sort_by == "price_low_to_high":
            return sorted(schedules, key=lambda x: x["base_price"])
        elif sort_by == "price_high_to_low":
            return sorted(schedules, key=lambda x: x["base_price"], reverse=True)
        elif sort_by == "duration_shortest":
            return sorted(schedules, key=lambda x: x["duration_minutes"])
        elif sort_by == "duration_longest":
            return sorted(schedules, key=lambda x: x["duration_minutes"], reverse=True)
        elif sort_by == "departure_time":
            return sorted(schedules, key=lambda x: x["departure_time"])
        elif sort_by == "arrival_time":
            return sorted(schedules, key=lambda x: x["arrival_time"])
        elif sort_by == "provider":
            return sorted(schedules, key=lambda x: x["provider_name"])
        else:
            # Default to departure time
            return sorted(schedules, key=lambda x: x["departure_time"])

    @staticmethod
    def get_price_comparison_summary(
        schedules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get price comparison summary for search results."""
        if not schedules:
            return {
                "total_options": 0,
                "price_range": {"min": 0, "max": 0, "average": 0},
                "provider_count": 0,
                "departure_times": {"earliest": None, "latest": None},
                "duration_range": {"min": 0, "max": 0, "average": 0}
            }
        
        prices = [s["base_price"] for s in schedules]
        durations = [s["duration_minutes"] for s in schedules]
        providers = set(s["provider_code"] for s in schedules)
        departure_times = [datetime.fromisoformat(s["departure_time"]) for s in schedules]
        
        return {
            "total_options": len(schedules),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices)
            },
            "provider_count": len(providers),
            "departure_times": {
                "earliest": min(departure_times).isoformat(),
                "latest": max(departure_times).isoformat()
            },
            "duration_range": {
                "min": min(durations),
                "max": max(durations),
                "average": sum(durations) / len(durations)
            },
            "providers": list(providers)
        }

    @staticmethod
    async def initialize_mock_providers(session: AsyncSession) -> List[TransportProvider]:
        """Initialize mock transport providers in the database."""
        providers = []
        
        for code, data in TransportProviderService.MOCK_PROVIDERS.items():
            provider = await TransportProviderService.create_or_update_provider(
                session=session,
                name=data["name"],
                code=data["code"],
                website_url=data["website"],
                contact_email=data.get("email"),
                contact_phone=data.get("phone"),
                transport_type=TransportType.BUS
            )
            providers.append(provider)
        
        return providers