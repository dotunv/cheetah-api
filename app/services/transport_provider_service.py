import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
import random

from ..database.models import TransportProvider, Route, Schedule, TransportType
from ..database.config import get_settings


class TransportProviderService:
    """Service for managing transport provider integrations and data."""
    
    # Mock data for transport providers
    MOCK_PROVIDERS = {
        "abc_transport": {
            "name": "ABC Transport",
            "code": "abc",
            "website": "https://www.abctransport.com/",
            "routes": [
                {"origin": "Lagos", "destination": "Abuja", "duration_hours": 12},
                {"origin": "Lagos", "destination": "Port Harcourt", "duration_hours": 8},
                {"origin": "Lagos", "destination": "Calabar", "duration_hours": 10},
                {"origin": "Abuja", "destination": "Lagos", "duration_hours": 12},
                {"origin": "Port Harcourt", "destination": "Lagos", "duration_hours": 8},
                {"origin": "Calabar", "destination": "Lagos", "duration_hours": 10},
                {"origin": "Lagos", "destination": "Owerri", "duration_hours": 7},
                {"origin": "Owerri", "destination": "Lagos", "duration_hours": 7},
            ]
        },
        "guo_transport": {
            "name": "G.U.O Transport",
            "code": "guo",
            "website": "https://guotransport.com/",
            "routes": [
                {"origin": "Lagos", "destination": "Enugu", "duration_hours": 9},
                {"origin": "Lagos", "destination": "Kano", "duration_hours": 15},
                {"origin": "Lagos", "destination": "Kaduna", "duration_hours": 13},
                {"origin": "Enugu", "destination": "Lagos", "duration_hours": 9},
                {"origin": "Kano", "destination": "Lagos", "duration_hours": 15},
                {"origin": "Kaduna", "destination": "Lagos", "duration_hours": 13},
                {"origin": "Lagos", "destination": "Jos", "duration_hours": 11},
                {"origin": "Jos", "destination": "Lagos", "duration_hours": 11},
            ]
        },
        "pmt": {
            "name": "PMT",
            "code": "pmt",
            "website": "https://pmt.ng/",
            "routes": [
                {"origin": "Lagos", "destination": "Ibadan", "duration_hours": 3},
                {"origin": "Lagos", "destination": "Ilorin", "duration_hours": 6},
                {"origin": "Lagos", "destination": "Akure", "duration_hours": 5},
                {"origin": "Ibadan", "destination": "Lagos", "duration_hours": 3},
                {"origin": "Ilorin", "destination": "Lagos", "duration_hours": 6},
                {"origin": "Akure", "destination": "Lagos", "duration_hours": 5},
                {"origin": "Lagos", "destination": "Ado Ekiti", "duration_hours": 4},
                {"origin": "Ado Ekiti", "destination": "Lagos", "duration_hours": 4},
            ]
        }
    }
    
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
        
        # Sort by departure time
        all_schedules.sort(key=lambda x: x["departure_time"])
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
            existing_provider.updated_at = datetime.utcnow()

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

        # Find matching route
        matching_route = None
        for route in provider_data["routes"]:
            if (route["origin"].lower() == origin.lower() and 
                route["destination"].lower() == destination.lower()):
                matching_route = route
                break

        if not matching_route:
            return []

        # Generate mock schedules for the date
        schedules = []
        base_times = ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]

        for i, base_time in enumerate(base_times):
            # Skip some schedules randomly for realism
            if random.random() < 0.3:
                continue

            departure_time = datetime.combine(date.date(), datetime.strptime(base_time, "%H:%M").time())
            duration_hours = matching_route["duration_hours"]
            arrival_time = departure_time + timedelta(hours=duration_hours)

            # Generate random pricing based on distance and time
            base_price = 5000 + (duration_hours * 500) + random.randint(-500, 1000)

            # Generate random seat availability
            total_seats = random.choice([18, 24, 30, 45])
            available_seats = random.randint(5, total_seats)

            # Vehicle types
            vehicle_types = ["Sprinter", "Luxury Bus", "AC Bus", "Shuttle"]
            vehicle_type = random.choice(vehicle_types)

            # Amenities
            if "Luxury" in vehicle_type:
                amenities = ["AC", "WiFi", "USB Charging", "Reclining Seats", "Entertainment"]
            elif "AC" in vehicle_type:
                amenities = ["AC", "USB Charging", "Reclining Seats"]
            else:
                amenities = ["USB Charging"]

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
                "base_price": base_price,
                "vehicle_type": vehicle_type,
                "amenities": amenities,
                "provider_name": provider_data["name"]
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
        base_price = 5000 + random.randint(1000, 3000)
        total_price = base_price * seats
        booking_fee = 200
        insurance_fee = 0
        wifi_fee = 0

        return {
            "schedule_id": schedule_id,
            "provider_code": provider_code,
            "base_price_per_seat": base_price,
            "seats_requested": seats,
            "total_price": total_price,
            "booking_fee": booking_fee,
            "insurance_fee": insurance_fee,
            "wifi_fee": wifi_fee,
            "grand_total": total_price + booking_fee
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
                "booking_time": datetime.utcnow().isoformat()
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
            
        if "min_seats" in filters:
            filtered = [s for s in filtered if s["available_seats"] >= filters["min_seats"]]
            
        if "vehicle_type" in filters:
            filtered = [s for s in filtered if filters["vehicle_type"] in s["vehicle_type"]]
            
        if "amenities" in filters:
            amenities = set(filters["amenities"])
            filtered = [s for s in filtered if amenities.issubset(set(s["amenities"]))]
            
        return filtered

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
                transport_type=TransportType.BUS
            )
            providers.append(provider)
        
        return providers