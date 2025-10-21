#!/usr/bin/env python3
"""
Database seeding script for Cheetah API.
Creates comprehensive mock data for testing and development.
"""

import asyncio
import json
import random
import string
from datetime import datetime, timedelta
from typing import List
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import database components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import AsyncSessionLocal, engine
from app.database.models import (
    User, TransportProvider, Route, Schedule, Booking,
    InsurancePolicy, WifiCode, UserRole, TransportType,
    BookingStatus, PaymentStatus, InsuranceStatus, WifiUsageStatus
)

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def generate_booking_reference() -> str:
    """Generate a unique booking reference."""
    return f"CH{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

def generate_policy_number() -> str:
    """Generate a unique insurance policy number."""
    return f"POL{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"

def generate_wifi_code() -> str:
    """Generate a unique WiFi access code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def hash_password(password: str) -> str:
    """Hash a password."""
    # Truncate password to 72 bytes for bcrypt compatibility
    password = password[:72]
    return pwd_context.hash(password)

# Mock data
TRANSPORT_PROVIDERS = [
    {
        "name": "ABC Transport",
        "code": "abc",
        "transport_type": TransportType.BUS,
        "contact_email": "info@abctransport.com",
        "contact_phone": "+234-1-234-5678",
        "website_url": "https://abctransport.com",
        "api_endpoint": "https://api.abctransport.com/v1",
        "api_key": "abc_api_key_123"
    },
    {
        "name": "G.U.O Transport",
        "code": "guo",
        "transport_type": TransportType.BUS,
        "contact_email": "support@guotransport.com",
        "contact_phone": "+234-1-876-5432",
        "website_url": "https://guotransport.com",
        "api_endpoint": "https://api.guotransport.com/v1",
        "api_key": "guo_api_key_456"
    },
    {
        "name": "Peace Mass Transit (PMT)",
        "code": "pmt",
        "transport_type": TransportType.BUS,
        "contact_email": "contact@peacemass.com",
        "contact_phone": "+234-1-345-6789",
        "website_url": "https://peacemass.com",
        "api_endpoint": "https://api.peacemass.com/v1",
        "api_key": "pmt_api_key_789"
    },
    {
        "name": "Young Shall Grow Motors",
        "code": "ysg",
        "transport_type": TransportType.BUS,
        "contact_email": "info@youngshallgrow.com",
        "contact_phone": "+234-1-456-7890",
        "website_url": "https://youngshallgrow.com",
        "api_endpoint": "https://api.youngshallgrow.com/v1",
        "api_key": "ysg_api_key_101"
    }
]

ROUTES = [
    # Lagos routes
    {"origin": "Lagos", "destination": "Abuja", "distance_km": 750, "duration_hours": 10},
    {"origin": "Lagos", "destination": "Kano", "distance_km": 950, "duration_hours": 12},
    {"origin": "Lagos", "destination": "Port Harcourt", "distance_km": 650, "duration_hours": 8},
    {"origin": "Lagos", "destination": "Jos", "distance_km": 850, "duration_hours": 11},
    {"origin": "Lagos", "destination": "Kaduna", "distance_km": 800, "duration_hours": 10.5},
    {"origin": "Lagos", "destination": "Ibadan", "distance_km": 150, "duration_hours": 2.5},
    {"origin": "Lagos", "destination": "Enugu", "distance_km": 550, "duration_hours": 7},
    {"origin": "Lagos", "destination": "Calabar", "distance_km": 750, "duration_hours": 9},
    
    # Abuja routes
    {"origin": "Abuja", "destination": "Lagos", "distance_km": 750, "duration_hours": 10},
    {"origin": "Abuja", "destination": "Kano", "distance_km": 350, "duration_hours": 5},
    {"origin": "Abuja", "destination": "Jos", "distance_km": 200, "duration_hours": 3},
    {"origin": "Abuja", "destination": "Kaduna", "distance_km": 150, "duration_hours": 2},
    {"origin": "Abuja", "destination": "Port Harcourt", "distance_km": 650, "duration_hours": 8},
    {"origin": "Abuja", "destination": "Enugu", "distance_km": 450, "duration_hours": 6},
    
    # Kano routes
    {"origin": "Kano", "destination": "Lagos", "distance_km": 950, "duration_hours": 12},
    {"origin": "Kano", "destination": "Abuja", "distance_km": 350, "duration_hours": 5},
    {"origin": "Kano", "destination": "Kaduna", "distance_km": 200, "duration_hours": 3},
    {"origin": "Kano", "destination": "Jos", "distance_km": 400, "duration_hours": 6},
    
    # Other major routes
    {"origin": "Port Harcourt", "destination": "Lagos", "distance_km": 650, "duration_hours": 8},
    {"origin": "Port Harcourt", "destination": "Abuja", "distance_km": 650, "duration_hours": 8},
    {"origin": "Enugu", "destination": "Lagos", "distance_km": 550, "duration_hours": 7},
    {"origin": "Enugu", "destination": "Abuja", "distance_km": 450, "duration_hours": 6},
    {"origin": "Jos", "destination": "Lagos", "distance_km": 850, "duration_hours": 11},
    {"origin": "Jos", "destination": "Abuja", "distance_km": 200, "duration_hours": 3},
]

VEHICLE_TYPES = [
    "Luxury Bus", "Executive Bus", "Standard Bus", "Sprinter", "Hiace",
    "Coaster", "Mercedes-Benz", "Volvo", "Scania", "MAN"
]

AMENITIES = [
    "WiFi", "Air Conditioning", "Reclining Seats", "Entertainment System",
    "Charging Points", "Reading Light", "Blanket", "Pillow", "Water",
    "Snacks", "Toilet", "Refreshments", "Newspaper", "Magazine"
]

NIGERIAN_CITIES = [
    "Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt", "Kaduna", "Jos",
    "Ilorin", "Enugu", "Maiduguri", "Zaria", "Aba", "Ife", "Ikorodu",
    "Oyo", "Akure", "Abeokuta", "Sokoto", "Onitsha", "Warri", "Calabar"
]

FIRST_NAMES = [
    "Adebayo", "Aisha", "Chinedu", "Fatima", "Ibrahim", "Kemi", "Mohammed",
    "Ngozi", "Oluwaseun", "Rukayat", "Samuel", "Temitope", "Yusuf", "Zainab",
    "Emeka", "Funmi", "Hassan", "Ifeoma", "Jibril", "Kemi", "Ladi", "Musa",
    "Nkechi", "Obi", "Patience", "Rashida", "Sade", "Tunde", "Uche", "Victoria"
]

LAST_NAMES = [
    "Adebayo", "Ahmed", "Akintola", "Balogun", "Chukwu", "Dauda", "Eze",
    "Falana", "Garba", "Hassan", "Ibrahim", "Johnson", "Kolawole", "Lawal",
    "Mohammed", "Nwosu", "Okafor", "Peters", "Quadri", "Raji", "Salau",
    "Tijani", "Umar", "Victor", "Williams", "Yakubu", "Zakari"
]

async def create_users(session: AsyncSession) -> List[User]:
    """Create mock users."""
    users = []
    
    # Create admin user
    admin = User(
        email="admin@cheetah.com",
        phone="+234-800-000-0001",
        first_name="System",
        last_name="Administrator",
        hashed_password=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    users.append(admin)
    session.add(admin)
    
    # Create provider users
    for i, provider_data in enumerate(TRANSPORT_PROVIDERS):
        provider_user = User(
            email=f"provider{i+1}@{provider_data['code']}.com",
            phone=f"+234-800-000-{1000+i}",
            first_name=provider_data['name'].split()[0],
            last_name="Manager",
            hashed_password=hash_password("provider123"),
            role=UserRole.PROVIDER,
            is_active=True,
            is_verified=True
        )
        users.append(provider_user)
        session.add(provider_user)
    
    # Create customer users
    for i in range(50):  # Create 50 customer users
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i+1}@email.com"
        phone = f"+234-{random.randint(700, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        customer = User(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password("customer123"),
            role=UserRole.CUSTOMER,
            is_active=random.choice([True, True, True, False]),  # 75% active
            is_verified=random.choice([True, True, False])  # 67% verified
        )
        users.append(customer)
        session.add(customer)
    
    await session.commit()
    return users

async def create_transport_providers(session: AsyncSession) -> List[TransportProvider]:
    """Create transport providers."""
    providers = []
    
    for provider_data in TRANSPORT_PROVIDERS:
        provider = TransportProvider(**provider_data)
        providers.append(provider)
        session.add(provider)
    
    await session.commit()
    return providers

async def create_routes(session: AsyncSession, providers: List[TransportProvider]) -> List[Route]:
    """Create routes for each provider."""
    routes = []
    
    for provider in providers:
        # Each provider gets a subset of routes
        provider_routes = random.sample(ROUTES, random.randint(8, 15))
        
        for i, route_data in enumerate(provider_routes):
            route = Route(
                provider_id=provider.id,
                origin=route_data["origin"],
                destination=route_data["destination"],
                route_code=f"{provider.code.upper()}{i+1:03d}",
                distance_km=route_data["distance_km"],
                estimated_duration_hours=route_data["duration_hours"],
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            routes.append(route)
            session.add(route)
    
    await session.commit()
    return routes

async def create_schedules(session: AsyncSession, routes: List[Route], providers: List[TransportProvider]) -> List[Schedule]:
    """Create schedules for routes."""
    schedules = []
    
    # Create provider lookup
    provider_lookup = {p.id: p for p in providers}
    
    for route in routes:
        if not route.is_active:
            continue
            
        provider = provider_lookup[route.provider_id]
        
        # Create 2-4 schedules per route
        num_schedules = random.randint(2, 4)
        
        for i in range(num_schedules):
            # Generate departure time (next 30 days, various times)
            days_ahead = random.randint(1, 30)
            hour = random.choice([6, 8, 10, 12, 14, 16, 18, 20, 22])
            departure_time = datetime.now() + timedelta(days=days_ahead, hours=hour)
            
            # Calculate arrival time
            duration_minutes = int(route.estimated_duration_hours * 60)
            arrival_time = departure_time + timedelta(minutes=duration_minutes)
            
            # Generate pricing based on distance
            base_price = route.distance_km * random.uniform(15, 25)  # 15-25 Naira per km
            
            # Vehicle capacity
            total_seats = random.choice([14, 18, 30, 45, 49, 55, 60])
            available_seats = random.randint(5, total_seats)
            
            # Generate amenities (JSON string)
            num_amenities = random.randint(3, 8)
            selected_amenities = random.sample(AMENITIES, num_amenities)
            amenities_json = json.dumps(selected_amenities)
            
            schedule = Schedule(
                provider_id=route.provider_id,
                route_id=route.id,
                schedule_code=f"{provider.code.upper()}{route.route_code}{i+1}",
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration_minutes=duration_minutes,
                total_seats=total_seats,
                available_seats=available_seats,
                base_price=base_price,
                vehicle_type=random.choice(VEHICLE_TYPES),
                amenities=amenities_json,
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            schedules.append(schedule)
            session.add(schedule)
    
    await session.commit()
    return schedules

async def create_bookings(session: AsyncSession, schedules: List[Schedule], users: List[User]) -> List[Booking]:
    """Create bookings."""
    bookings = []
    
    # Filter active schedules and customer users
    active_schedules = [s for s in schedules if s.is_active]
    customer_users = [u for u in users if u.role == UserRole.CUSTOMER and u.is_active]
    
    # Create bookings for some schedules
    for schedule in random.sample(active_schedules, min(100, len(active_schedules))):
        # Create 1-5 bookings per schedule
        num_bookings = random.randint(1, 5)
        
        for i in range(num_bookings):
            # Decide if it's a guest booking or user booking
            is_guest_booking = random.choice([True, False])
            
            if is_guest_booking:
                user_id = None
                guest_email = f"guest{i+1}@email.com"
                guest_phone = f"+234-{random.randint(700, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            else:
                user_id = random.choice(customer_users).id
                guest_email = None
                guest_phone = None
            
            # Passenger details (JSON)
            passenger_count = random.randint(1, 4)
            passenger_details = []
            for j in range(passenger_count):
                passenger_details.append({
                    "first_name": random.choice(FIRST_NAMES),
                    "last_name": random.choice(LAST_NAMES),
                    "phone": f"+234-{random.randint(700, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "seat_number": f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 15)}"
                })
            
            # Calculate total amount
            total_amount = schedule.base_price * passenger_count
            
            # Booking and payment status
            booking_status = random.choices(
                [BookingStatus.CONFIRMED, BookingStatus.PENDING, BookingStatus.COMPLETED, BookingStatus.CANCELLED],
                weights=[60, 15, 20, 5]
            )[0]
            
            payment_status = random.choices(
                [PaymentStatus.PAID, PaymentStatus.PENDING, PaymentStatus.FAILED, PaymentStatus.REFUNDED],
                weights=[70, 15, 10, 5]
            )[0]
            
            # Provider booking reference
            provider_ref = f"REF{random.randint(100000, 999999)}"
            
            booking = Booking(
                booking_reference=generate_booking_reference(),
                user_id=user_id,
                guest_email=guest_email,
                guest_phone=guest_phone,
                schedule_id=schedule.id,
                passenger_count=passenger_count,
                total_amount=total_amount,
                booking_status=booking_status,
                payment_status=payment_status,
                passenger_details=json.dumps(passenger_details),
                provider_booking_reference=provider_ref,
                notes=random.choice([
                    "Window seat preferred",
                    "Accessible seat required",
                    "Vegetarian meal",
                    "Early check-in",
                    None, None, None  # 50% chance of no notes
                ])
            )
            bookings.append(booking)
            session.add(booking)
    
    await session.commit()
    return bookings

async def create_insurance_policies(session: AsyncSession, bookings: List[Booking], users: List[User]) -> List[InsurancePolicy]:
    """Create insurance policies for confirmed bookings."""
    policies = []
    
    # Create user lookup
    user_lookup = {u.id: u for u in users}
    
    # Filter confirmed bookings with users
    confirmed_bookings = [
        b for b in bookings 
        if b.booking_status == BookingStatus.CONFIRMED and b.user_id is not None
    ]
    
    for booking in confirmed_bookings[:30]:  # Create policies for 30 bookings
        user = user_lookup[booking.user_id]
        
        # Policy dates
        start_date = booking.created_at
        end_date = start_date + timedelta(days=1)  # 24-hour coverage
        
        # Coverage amount
        coverage_amount = random.uniform(500000, 2000000)  # 500K - 2M Naira
        
        policy = InsurancePolicy(
            booking_id=booking.id,
            user_id=user.id,
            policy_number=generate_policy_number(),
            coverage_details_url=f"https://insurance.cheetah.com/policy/{booking.booking_reference}",
            status=random.choice([InsuranceStatus.ACTIVE, InsuranceStatus.EXPIRED]),
            start_date=start_date,
            end_date=end_date,
            coverage_amount=coverage_amount,
            provider_policy_id=f"INS{random.randint(100000, 999999)}"
        )
        policies.append(policy)
        session.add(policy)
    
    await session.commit()
    return policies

async def create_wifi_codes(session: AsyncSession, bookings: List[Booking]) -> List[WifiCode]:
    """Create WiFi codes for confirmed bookings."""
    wifi_codes = []
    
    # Filter confirmed bookings
    confirmed_bookings = [
        b for b in bookings 
        if b.booking_status == BookingStatus.CONFIRMED
    ]
    
    for booking in confirmed_bookings[:25]:  # Create WiFi codes for 25 bookings
        # Expiry time (24 hours from booking creation)
        expiry_time = booking.created_at + timedelta(hours=24)
        
        # Bandwidth limit
        bandwidth_limit = random.choice([250, 500, 1000])  # MB
        
        wifi_code = WifiCode(
            booking_id=booking.id,
            code=generate_wifi_code(),
            qr_code_data=f"https://wifi.cheetah.com/qr/{booking.booking_reference}",
            expiry_time=expiry_time,
            usage_status=random.choices(
                [WifiUsageStatus.UNUSED, WifiUsageStatus.ACTIVE, WifiUsageStatus.USED, WifiUsageStatus.EXPIRED],
                weights=[40, 20, 30, 10]
            )[0],
            bandwidth_limit_mb=bandwidth_limit,
            provider_code_id=f"WIFI{random.randint(100000, 999999)}"
        )
        wifi_codes.append(wifi_code)
        session.add(wifi_code)
    
    await session.commit()
    return wifi_codes

async def main():
    """Main seeding function."""
    print("🌱 Starting database seeding...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Create all entities
            print("👥 Creating users...")
            users = await create_users(session)
            print(f"✅ Created {len(users)} users")
            
            print("🚌 Creating transport providers...")
            providers = await create_transport_providers(session)
            print(f"✅ Created {len(providers)} transport providers")
            
            print("🛣️ Creating routes...")
            routes = await create_routes(session, providers)
            print(f"✅ Created {len(routes)} routes")
            
            print("📅 Creating schedules...")
            schedules = await create_schedules(session, routes, providers)
            print(f"✅ Created {len(schedules)} schedules")
            
            print("🎫 Creating bookings...")
            bookings = await create_bookings(session, schedules, users)
            print(f"✅ Created {len(bookings)} bookings")
            
            print("🛡️ Creating insurance policies...")
            policies = await create_insurance_policies(session, bookings, users)
            print(f"✅ Created {len(policies)} insurance policies")
            
            print("📶 Creating WiFi codes...")
            wifi_codes = await create_wifi_codes(session, bookings)
            print(f"✅ Created {len(wifi_codes)} WiFi codes")
            
            print("\n🎉 Database seeding completed successfully!")
            print("\n📊 Summary:")
            print(f"   • Users: {len(users)}")
            print(f"   • Transport Providers: {len(providers)}")
            print(f"   • Routes: {len(routes)}")
            print(f"   • Schedules: {len(schedules)}")
            print(f"   • Bookings: {len(bookings)}")
            print(f"   • Insurance Policies: {len(policies)}")
            print(f"   • WiFi Codes: {len(wifi_codes)}")
            
            print("\n🔑 Default Login Credentials:")
            print("   • Admin: admin@cheetah.com / admin123")
            print("   • Provider: provider1@abc.com / provider123")
            print("   • Customer: [any customer email] / customer123")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main())
