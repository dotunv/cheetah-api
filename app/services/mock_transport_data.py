"""
Extensive mock data for transport services in Nigeria.
This module contains comprehensive mock data that transport providers would typically use.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import random


class MockTransportData:
    """Comprehensive mock data for Nigerian transport services."""
    
    # Nigerian cities and states with realistic distances and travel times
    CITIES = {
        "Lagos": {
            "state": "Lagos",
            "zone": "South West",
            "coordinates": {"lat": 6.5244, "lng": 3.3792},
            "terminals": ["Jibowu", "Ojota", "Mile 2", "Oshodi", "Festac"]
        },
        "Abuja": {
            "state": "FCT",
            "zone": "North Central",
            "coordinates": {"lat": 9.0765, "lng": 7.3986},
            "terminals": ["Jabi", "Gwagwalada", "Kubwa", "Nyanya", "Karu"]
        },
        "Kano": {
            "state": "Kano",
            "zone": "North West",
            "coordinates": {"lat": 12.0022, "lng": 8.5920},
            "terminals": ["Kofar Nassarawa", "Sabon Gari", "Bompai", "Tudun Wada"]
        },
        "Port Harcourt": {
            "state": "Rivers",
            "zone": "South South",
            "coordinates": {"lat": 4.8156, "lng": 7.0498},
            "terminals": ["Mile 1", "Rumuokoro", "Eleme", "Ogbunabali"]
        },
        "Ibadan": {
            "state": "Oyo",
            "zone": "South West",
            "coordinates": {"lat": 7.3776, "lng": 3.9470},
            "terminals": ["Challenge", "Mokola", "Sango", "Bodija"]
        },
        "Kaduna": {
            "state": "Kaduna",
            "zone": "North West",
            "coordinates": {"lat": 10.5200, "lng": 7.4381},
            "terminals": ["Kakuri", "Rigasa", "Ungwan Rimi", "Sabon Tasha"]
        },
        "Enugu": {
            "state": "Enugu",
            "zone": "South East",
            "coordinates": {"lat": 6.4412, "lng": 7.4988},
            "terminals": ["Garki", "Abakpa", "New Haven", "Independence Layout"]
        },
        "Calabar": {
            "state": "Cross River",
            "zone": "South South",
            "coordinates": {"lat": 4.9515, "lng": 8.3228},
            "terminals": ["Marian", "Watt", "Etta Agbor", "Atimbo"]
        },
        "Jos": {
            "state": "Plateau",
            "zone": "North Central",
            "coordinates": {"lat": 9.9170, "lng": 8.9001},
            "terminals": ["Terminus", "Bukuru", "Rayfield", "Angwan Rukuba"]
        },
        "Owerri": {
            "state": "Imo",
            "zone": "South East",
            "coordinates": {"lat": 5.4920, "lng": 7.0260},
            "terminals": ["Aladinma", "Wetheral", "Douglas", "New Owerri"]
        },
        "Ilorin": {
            "state": "Kwara",
            "zone": "North Central",
            "coordinates": {"lat": 8.4969, "lng": 4.5421},
            "terminals": ["Ganmo", "Maraba", "Oja Oba", "Challenge"]
        },
        "Akure": {
            "state": "Ondo",
            "zone": "South West",
            "coordinates": {"lat": 7.2574, "lng": 5.2058},
            "terminals": ["Oja Oba", "Oba Ile", "Alagbaka", "Ondo Road"]
        },
        "Ado Ekiti": {
            "state": "Ekiti",
            "zone": "South West",
            "coordinates": {"lat": 7.6233, "lng": 5.2210},
            "terminals": ["Oja Oba", "Fajuyi", "Ondo Road", "Ilawe Road"]
        },
        "Maiduguri": {
            "state": "Borno",
            "zone": "North East",
            "coordinates": {"lat": 11.8333, "lng": 13.1500},
            "terminals": ["Monday Market", "Customs", "Baga Road", "Gamboru"]
        },
        "Yola": {
            "state": "Adamawa",
            "zone": "North East",
            "coordinates": {"lat": 9.2035, "lng": 12.4954},
            "terminals": ["Jimeta", "Doubeli", "Yolde Pate", "Numan Road"]
        },
        "Bauchi": {
            "state": "Bauchi",
            "zone": "North East",
            "coordinates": {"lat": 10.3103, "lng": 9.8439},
            "terminals": ["Wunti", "Railway", "Gwallaga", "Dass Road"]
        },
        "Katsina": {
            "state": "Katsina",
            "zone": "North West",
            "coordinates": {"lat": 12.9908, "lng": 7.6018},
            "terminals": ["Kofar Kaura", "Dutsinma", "Kankara", "Mani"]
        },
        "Sokoto": {
            "state": "Sokoto",
            "zone": "North West",
            "coordinates": {"lat": 13.0059, "lng": 5.2476},
            "terminals": ["Central Market", "Rijiya", "Gidan Kwano", "Kebbe"]
        },
        "Zaria": {
            "state": "Kaduna",
            "zone": "North West",
            "coordinates": {"lat": 11.1112, "lng": 7.7227},
            "terminals": ["Samaru", "Tudun Wada", "Sabon Gari", "Kofar Gayan"]
        },
        "Abeokuta": {
            "state": "Ogun",
            "zone": "South West",
            "coordinates": {"lat": 7.1557, "lng": 3.3451},
            "terminals": ["Kuto", "Ita Eko", "Sapon", "Adatan"]
        }
    }
    
    # Distance matrix between major cities (in kilometers)
    DISTANCE_MATRIX = {
        ("Lagos", "Abuja"): 750,
        ("Lagos", "Kano"): 1000,
        ("Lagos", "Port Harcourt"): 600,
        ("Lagos", "Ibadan"): 150,
        ("Lagos", "Kaduna"): 900,
        ("Lagos", "Enugu"): 650,
        ("Lagos", "Calabar"): 700,
        ("Lagos", "Jos"): 800,
        ("Lagos", "Owerri"): 500,
        ("Lagos", "Ilorin"): 300,
        ("Lagos", "Akure"): 250,
        ("Lagos", "Ado Ekiti"): 200,
        ("Lagos", "Abeokuta"): 100,
        ("Abuja", "Kano"): 400,
        ("Abuja", "Kaduna"): 200,
        ("Abuja", "Jos"): 300,
        ("Abuja", "Enugu"): 400,
        ("Abuja", "Ilorin"): 350,
        ("Kano", "Kaduna"): 200,
        ("Kano", "Katsina"): 150,
        ("Kano", "Sokoto"): 300,
        ("Kano", "Zaria"): 100,
        ("Port Harcourt", "Calabar"): 200,
        ("Port Harcourt", "Owerri"): 150,
        ("Enugu", "Owerri"): 100,
        ("Jos", "Kaduna"): 250,
        ("Ibadan", "Ilorin"): 200,
        ("Ibadan", "Akure"): 150,
        ("Ibadan", "Abeokuta"): 100,
        ("Akure", "Ado Ekiti"): 50
    }
    
    # Vehicle types with realistic specifications
    VEHICLE_TYPES = {
        "Sprinter": {
            "capacity": 18,
            "base_price_per_km": 15,
            "amenities": ["AC", "USB Charging"],
            "comfort_level": "Standard",
            "fuel_efficiency": "High"
        },
        "Luxury Bus": {
            "capacity": 45,
            "base_price_per_km": 25,
            "amenities": ["AC", "WiFi", "USB Charging", "Reclining Seats", "Entertainment", "Toilet"],
            "comfort_level": "Premium",
            "fuel_efficiency": "Medium"
        },
        "AC Bus": {
            "capacity": 30,
            "base_price_per_km": 20,
            "amenities": ["AC", "USB Charging", "Reclining Seats"],
            "comfort_level": "Comfortable",
            "fuel_efficiency": "Medium"
        },
        "Shuttle": {
            "capacity": 14,
            "base_price_per_km": 12,
            "amenities": ["AC"],
            "comfort_level": "Basic",
            "fuel_efficiency": "High"
        },
        "Executive Bus": {
            "capacity": 25,
            "base_price_per_km": 30,
            "amenities": ["AC", "WiFi", "USB Charging", "Reclining Seats", "Entertainment", "Refreshments", "Toilet"],
            "comfort_level": "Executive",
            "fuel_efficiency": "Low"
        },
        "Mini Bus": {
            "capacity": 12,
            "base_price_per_km": 10,
            "amenities": ["AC"],
            "comfort_level": "Basic",
            "fuel_efficiency": "Very High"
        }
    }
    
    # Comprehensive transport providers with realistic data
    TRANSPORT_PROVIDERS = {
        "abc": {
            "name": "ABC Transport Company Limited",
            "code": "abc",
            "website": "https://www.abctransport.com.ng/",
            "phone": "+234-1-234-5678",
            "email": "info@abctransport.com.ng",
            "founded": 1985,
            "fleet_size": 150,
            "coverage": ["South West", "North Central", "South South"],
            "specialties": ["Luxury Bus", "AC Bus"],
            "reputation": "Excellent",
            "safety_rating": 4.8,
            "routes": [
                {"origin": "Lagos", "destination": "Abuja", "duration_hours": 12, "frequency": "hourly"},
                {"origin": "Lagos", "destination": "Port Harcourt", "duration_hours": 8, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Calabar", "duration_hours": 10, "frequency": "daily"},
                {"origin": "Abuja", "destination": "Lagos", "duration_hours": 12, "frequency": "hourly"},
                {"origin": "Port Harcourt", "destination": "Lagos", "duration_hours": 8, "frequency": "every_2_hours"},
                {"origin": "Calabar", "destination": "Lagos", "duration_hours": 10, "frequency": "daily"},
                {"origin": "Lagos", "destination": "Owerri", "duration_hours": 7, "frequency": "every_3_hours"},
                {"origin": "Owerri", "destination": "Lagos", "duration_hours": 7, "frequency": "every_3_hours"},
                {"origin": "Lagos", "destination": "Ibadan", "duration_hours": 3, "frequency": "every_30_minutes"},
                {"origin": "Ibadan", "destination": "Lagos", "duration_hours": 3, "frequency": "every_30_minutes"},
                {"origin": "Lagos", "destination": "Abeokuta", "duration_hours": 2, "frequency": "every_30_minutes"},
                {"origin": "Abeokuta", "destination": "Lagos", "duration_hours": 2, "frequency": "every_30_minutes"}
            ]
        },
        "guo": {
            "name": "G.U.O Transport Services Limited",
            "code": "guo",
            "website": "https://guotransport.com.ng/",
            "phone": "+234-1-234-5679",
            "email": "info@guotransport.com.ng",
            "founded": 1990,
            "fleet_size": 200,
            "coverage": ["North West", "North Central", "North East", "South East"],
            "specialties": ["Luxury Bus", "Executive Bus"],
            "reputation": "Very Good",
            "safety_rating": 4.6,
            "routes": [
                {"origin": "Lagos", "destination": "Enugu", "duration_hours": 9, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Kano", "duration_hours": 15, "frequency": "daily"},
                {"origin": "Lagos", "destination": "Kaduna", "duration_hours": 13, "frequency": "daily"},
                {"origin": "Enugu", "destination": "Lagos", "duration_hours": 9, "frequency": "every_2_hours"},
                {"origin": "Kano", "destination": "Lagos", "duration_hours": 15, "frequency": "daily"},
                {"origin": "Kaduna", "destination": "Lagos", "duration_hours": 13, "frequency": "daily"},
                {"origin": "Lagos", "destination": "Jos", "duration_hours": 11, "frequency": "daily"},
                {"origin": "Jos", "destination": "Lagos", "duration_hours": 11, "frequency": "daily"},
                {"origin": "Abuja", "destination": "Kano", "duration_hours": 4, "frequency": "every_2_hours"},
                {"origin": "Kano", "destination": "Abuja", "duration_hours": 4, "frequency": "every_2_hours"},
                {"origin": "Kaduna", "destination": "Kano", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Kano", "destination": "Kaduna", "duration_hours": 2, "frequency": "every_hour"}
            ]
        },
        "pmt": {
            "name": "Peace Mass Transit Limited",
            "code": "pmt",
            "website": "https://pmt.ng/",
            "phone": "+234-1-234-5680",
            "email": "info@pmt.ng",
            "founded": 1995,
            "fleet_size": 300,
            "coverage": ["South West", "North Central"],
            "specialties": ["Sprinter", "AC Bus", "Shuttle"],
            "reputation": "Good",
            "safety_rating": 4.2,
            "routes": [
                {"origin": "Lagos", "destination": "Ibadan", "duration_hours": 3, "frequency": "every_30_minutes"},
                {"origin": "Lagos", "destination": "Ilorin", "duration_hours": 6, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Akure", "duration_hours": 5, "frequency": "every_2_hours"},
                {"origin": "Ibadan", "destination": "Lagos", "duration_hours": 3, "frequency": "every_30_minutes"},
                {"origin": "Ilorin", "destination": "Lagos", "duration_hours": 6, "frequency": "every_2_hours"},
                {"origin": "Akure", "destination": "Lagos", "duration_hours": 5, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Ado Ekiti", "duration_hours": 4, "frequency": "every_2_hours"},
                {"origin": "Ado Ekiti", "destination": "Lagos", "duration_hours": 4, "frequency": "every_2_hours"},
                {"origin": "Ibadan", "destination": "Ilorin", "duration_hours": 3, "frequency": "every_hour"},
                {"origin": "Ilorin", "destination": "Ibadan", "duration_hours": 3, "frequency": "every_hour"},
                {"origin": "Akure", "destination": "Ado Ekiti", "duration_hours": 1, "frequency": "every_hour"},
                {"origin": "Ado Ekiti", "destination": "Akure", "duration_hours": 1, "frequency": "every_hour"}
            ]
        },
        "chisco": {
            "name": "Chisco Transport Nigeria Limited",
            "code": "chisco",
            "website": "https://chiscotransport.com/",
            "phone": "+234-1-234-5681",
            "email": "info@chiscotransport.com",
            "founded": 1980,
            "fleet_size": 180,
            "coverage": ["South East", "South South", "North Central"],
            "specialties": ["Luxury Bus", "Executive Bus"],
            "reputation": "Excellent",
            "safety_rating": 4.7,
            "routes": [
                {"origin": "Lagos", "destination": "Enugu", "duration_hours": 9, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Owerri", "duration_hours": 7, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Port Harcourt", "duration_hours": 8, "frequency": "every_2_hours"},
                {"origin": "Enugu", "destination": "Lagos", "duration_hours": 9, "frequency": "every_2_hours"},
                {"origin": "Owerri", "destination": "Lagos", "duration_hours": 7, "frequency": "every_2_hours"},
                {"origin": "Port Harcourt", "destination": "Lagos", "duration_hours": 8, "frequency": "every_2_hours"},
                {"origin": "Enugu", "destination": "Abuja", "duration_hours": 4, "frequency": "every_3_hours"},
                {"origin": "Abuja", "destination": "Enugu", "duration_hours": 4, "frequency": "every_3_hours"},
                {"origin": "Owerri", "destination": "Port Harcourt", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Port Harcourt", "destination": "Owerri", "duration_hours": 2, "frequency": "every_hour"}
            ]
        },
        "gigl": {
            "name": "God is Great Motors Limited",
            "code": "gigl",
            "website": "https://gigl.ng/",
            "phone": "+234-1-234-5682",
            "email": "info@gigl.ng",
            "founded": 1992,
            "fleet_size": 120,
            "coverage": ["South West", "North Central"],
            "specialties": ["Sprinter", "AC Bus"],
            "reputation": "Good",
            "safety_rating": 4.3,
            "routes": [
                {"origin": "Lagos", "destination": "Ibadan", "duration_hours": 3, "frequency": "every_hour"},
                {"origin": "Lagos", "destination": "Ilorin", "duration_hours": 6, "frequency": "every_3_hours"},
                {"origin": "Ibadan", "destination": "Lagos", "duration_hours": 3, "frequency": "every_hour"},
                {"origin": "Ilorin", "destination": "Lagos", "duration_hours": 6, "frequency": "every_3_hours"},
                {"origin": "Ibadan", "destination": "Ilorin", "duration_hours": 3, "frequency": "every_2_hours"},
                {"origin": "Ilorin", "destination": "Ibadan", "duration_hours": 3, "frequency": "every_2_hours"},
                {"origin": "Lagos", "destination": "Abeokuta", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Abeokuta", "destination": "Lagos", "duration_hours": 2, "frequency": "every_hour"}
            ]
        },
        "efex": {
            "name": "EFEX Express Limited",
            "code": "efex",
            "website": "https://efexexpress.com/",
            "phone": "+234-1-234-5683",
            "email": "info@efexexpress.com",
            "founded": 2000,
            "fleet_size": 80,
            "coverage": ["North West", "North Central"],
            "specialties": ["Sprinter", "Mini Bus"],
            "reputation": "Very Good",
            "safety_rating": 4.4,
            "routes": [
                {"origin": "Abuja", "destination": "Kano", "duration_hours": 4, "frequency": "every_2_hours"},
                {"origin": "Abuja", "destination": "Kaduna", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Abuja", "destination": "Jos", "duration_hours": 3, "frequency": "every_2_hours"},
                {"origin": "Kano", "destination": "Abuja", "duration_hours": 4, "frequency": "every_2_hours"},
                {"origin": "Kaduna", "destination": "Abuja", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Jos", "destination": "Abuja", "duration_hours": 3, "frequency": "every_2_hours"},
                {"origin": "Kano", "destination": "Kaduna", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Kaduna", "destination": "Kano", "duration_hours": 2, "frequency": "every_hour"},
                {"origin": "Kano", "destination": "Katsina", "duration_hours": 2, "frequency": "every_2_hours"},
                {"origin": "Katsina", "destination": "Kano", "duration_hours": 2, "frequency": "every_2_hours"}
            ]
        },
        "young_shall_grow": {
            "name": "Young Shall Grow Motors Limited",
            "code": "young_shall_grow",
            "website": "https://youngshallgrow.com/",
            "phone": "+234-1-234-5684",
            "email": "info@youngshallgrow.com",
            "founded": 1988,
            "fleet_size": 100,
            "coverage": ["South East", "South South"],
            "specialties": ["Luxury Bus", "AC Bus"],
            "reputation": "Good",
            "safety_rating": 4.1,
            "routes": [
                {"origin": "Lagos", "destination": "Enugu", "duration_hours": 9, "frequency": "daily"},
                {"origin": "Lagos", "destination": "Owerri", "duration_hours": 7, "frequency": "daily"},
                {"origin": "Lagos", "destination": "Port Harcourt", "duration_hours": 8, "frequency": "daily"},
                {"origin": "Enugu", "destination": "Lagos", "duration_hours": 9, "frequency": "daily"},
                {"origin": "Owerri", "destination": "Lagos", "duration_hours": 7, "frequency": "daily"},
                {"origin": "Port Harcourt", "destination": "Lagos", "duration_hours": 8, "frequency": "daily"},
                {"origin": "Enugu", "destination": "Owerri", "duration_hours": 2, "frequency": "every_2_hours"},
                {"origin": "Owerri", "destination": "Enugu", "duration_hours": 2, "frequency": "every_2_hours"}
            ]
        },
        "akwa_ibom_transport": {
            "name": "Akwa Ibom Transport Company",
            "code": "akwa_ibom",
            "website": "https://akwaibomtransport.com/",
            "phone": "+234-1-234-5685",
            "email": "info@akwaibomtransport.com",
            "founded": 1995,
            "fleet_size": 60,
            "coverage": ["South South"],
            "specialties": ["AC Bus", "Sprinter"],
            "reputation": "Good",
            "safety_rating": 4.0,
            "routes": [
                {"origin": "Lagos", "destination": "Uyo", "duration_hours": 9, "frequency": "daily"},
                {"origin": "Uyo", "destination": "Lagos", "duration_hours": 9, "frequency": "daily"},
                {"origin": "Port Harcourt", "destination": "Uyo", "duration_hours": 2, "frequency": "every_2_hours"},
                {"origin": "Uyo", "destination": "Port Harcourt", "duration_hours": 2, "frequency": "every_2_hours"},
                {"origin": "Calabar", "destination": "Uyo", "duration_hours": 3, "frequency": "every_2_hours"},
                {"origin": "Uyo", "destination": "Calabar", "duration_hours": 3, "frequency": "every_2_hours"}
            ]
        }
    }
    
    # Pricing tiers based on distance and vehicle type
    PRICING_TIERS = {
        "short_distance": {  # < 200km
            "base_price": 2000,
            "price_per_km": 8,
            "minimum_price": 1500
        },
        "medium_distance": {  # 200-500km
            "base_price": 3000,
            "price_per_km": 12,
            "minimum_price": 2500
        },
        "long_distance": {  # 500-800km
            "base_price": 5000,
            "price_per_km": 15,
            "minimum_price": 4000
        },
        "very_long_distance": {  # > 800km
            "base_price": 8000,
            "price_per_km": 18,
            "minimum_price": 6000
        }
    }
    
    # Time-based pricing multipliers
    TIME_MULTIPLIERS = {
        "early_morning": {"start": "05:00", "end": "08:00", "multiplier": 0.9},
        "morning": {"start": "08:00", "end": "12:00", "multiplier": 1.0},
        "afternoon": {"start": "12:00", "end": "16:00", "multiplier": 1.1},
        "evening": {"start": "16:00", "end": "20:00", "multiplier": 1.2},
        "night": {"start": "20:00", "end": "05:00", "multiplier": 1.3}
    }
    
    # Day-of-week pricing multipliers
    DAY_MULTIPLIERS = {
        "monday": 1.0,
        "tuesday": 1.0,
        "wednesday": 1.0,
        "thursday": 1.0,
        "friday": 1.2,  # Weekend rush
        "saturday": 1.3,  # Weekend
        "sunday": 1.1   # Weekend
    }
    
    # Seasonal pricing multipliers
    SEASONAL_MULTIPLIERS = {
        "normal": 1.0,
        "holiday": 1.5,  # Christmas, New Year, Easter
        "festival": 1.3,  # Local festivals
        "school_holiday": 1.2  # School breaks
    }
    
    # Common amenities and their descriptions
    AMENITIES = {
        "AC": "Air Conditioning",
        "WiFi": "Free WiFi Internet",
        "USB_Charging": "USB Charging Ports",
        "Reclining_Seats": "Reclining Seats",
        "Entertainment": "In-bus Entertainment System",
        "Toilet": "On-board Toilet",
        "Refreshments": "Complimentary Refreshments",
        "Blanket": "Blankets and Pillows",
        "Water": "Free Bottled Water",
        "Newspaper": "Daily Newspapers",
        "Magazine": "Travel Magazines",
        "Snacks": "Light Snacks",
        "Meal": "Full Meal Service",
        "Priority_Boarding": "Priority Boarding",
        "Luggage_Service": "Luggage Handling Service",
        "Insurance": "Travel Insurance",
        "Tracking": "Real-time GPS Tracking",
        "SMS_Updates": "SMS Updates",
        "Mobile_App": "Mobile App Integration",
        "Loyalty_Program": "Loyalty Program"
    }
    
    # Terminal facilities
    TERMINAL_FACILITIES = {
        "waiting_area": "Comfortable Waiting Area",
        "restaurant": "Restaurant/Food Court",
        "atm": "ATM Services",
        "wifi": "Free WiFi",
        "parking": "Secure Parking",
        "security": "24/7 Security",
        "luggage_storage": "Luggage Storage",
        "ticket_office": "Ticket Office",
        "information_desk": "Information Desk",
        "first_aid": "First Aid Station",
        "toilet": "Clean Toilets",
        "shop": "Convenience Shop",
        "pharmacy": "Pharmacy",
        "bank": "Banking Services",
        "hotel": "Nearby Hotels"
    }
    
    # Safety and compliance data
    SAFETY_STANDARDS = {
        "driver_qualification": "Professional Driver License",
        "vehicle_inspection": "Regular Vehicle Inspection",
        "insurance_coverage": "Comprehensive Insurance",
        "speed_limiting": "Speed Limiting Device",
        "gps_tracking": "GPS Tracking System",
        "emergency_contact": "24/7 Emergency Contact",
        "first_aid": "First Aid Training",
        "safety_briefing": "Passenger Safety Briefing",
        "seat_belts": "Seat Belt Enforcement",
        "child_safety": "Child Safety Seats"
    }
    
    # Booking policies
    BOOKING_POLICIES = {
        "advance_booking": "Book up to 30 days in advance",
        "cancellation": "Free cancellation up to 24 hours before departure",
        "refund_policy": "Full refund for cancellations made 24+ hours before departure",
        "modification": "Free modification up to 12 hours before departure",
        "no_show": "No refund for no-show passengers",
        "group_booking": "Special rates for groups of 10+ passengers",
        "student_discount": "10% discount for students with valid ID",
        "senior_discount": "15% discount for passengers 60+ years",
        "child_policy": "Children under 5 travel free, 5-12 years pay 50%",
        "luggage_allowance": "20kg free luggage allowance per passenger"
    }
    
    @classmethod
    def get_distance(cls, origin: str, destination: str) -> int:
        """Get distance between two cities in kilometers."""
        # Check both directions
        distance = cls.DISTANCE_MATRIX.get((origin, destination))
        if distance is None:
            distance = cls.DISTANCE_MATRIX.get((destination, origin))
        if distance is None:
            # Estimate based on coordinates if not in matrix
            return 500  # Default estimate
        return distance
    
    @classmethod
    def get_pricing_tier(cls, distance: int) -> str:
        """Get pricing tier based on distance."""
        if distance < 200:
            return "short_distance"
        elif distance < 500:
            return "medium_distance"
        elif distance < 800:
            return "long_distance"
        else:
            return "very_long_distance"
    
    @classmethod
    def calculate_base_price(cls, origin: str, destination: str, vehicle_type: str) -> float:
        """Calculate base price for a route."""
        distance = cls.get_distance(origin, destination)
        tier = cls.get_pricing_tier(distance)
        vehicle_specs = cls.VEHICLE_TYPES.get(vehicle_type, cls.VEHICLE_TYPES["AC Bus"])
        
        # Base calculation
        tier_pricing = cls.PRICING_TIERS[tier]
        base_price = tier_pricing["base_price"] + (distance * tier_pricing["price_per_km"])
        
        # Apply vehicle type multiplier
        vehicle_multiplier = vehicle_specs["base_price_per_km"] / 20  # Normalize to AC Bus
        base_price *= vehicle_multiplier
        
        # Ensure minimum price
        base_price = max(base_price, tier_pricing["minimum_price"])
        
        return round(base_price, 2)
    
    @classmethod
    def apply_time_multiplier(cls, base_price: float, departure_time: datetime) -> float:
        """Apply time-based pricing multiplier."""
        time_str = departure_time.strftime("%H:%M")
        
        for period, config in cls.TIME_MULTIPLIERS.items():
            start_time = datetime.strptime(config["start"], "%H:%M").time()
            end_time = datetime.strptime(config["end"], "%H:%M").time()
            current_time = departure_time.time()
            
            if start_time <= current_time < end_time or (config["start"] > config["end"] and (current_time >= start_time or current_time < end_time)):
                return base_price * config["multiplier"]
        
        return base_price
    
    @classmethod
    def apply_day_multiplier(cls, base_price: float, departure_time: datetime) -> float:
        """Apply day-of-week pricing multiplier."""
        day_name = departure_time.strftime("%A").lower()
        multiplier = cls.DAY_MULTIPLIERS.get(day_name, 1.0)
        return base_price * multiplier
    
    @classmethod
    def get_vehicle_amenities(cls, vehicle_type: str) -> List[str]:
        """Get amenities for a vehicle type."""
        vehicle_specs = cls.VEHICLE_TYPES.get(vehicle_type, cls.VEHICLE_TYPES["AC Bus"])
        return vehicle_specs["amenities"]
    
    @classmethod
    def get_route_frequency(cls, provider_code: str, origin: str, destination: str) -> str:
        """Get frequency for a specific route."""
        provider = cls.TRANSPORT_PROVIDERS.get(provider_code)
        if not provider:
            return "daily"
        
        for route in provider["routes"]:
            if route["origin"].lower() == origin.lower() and route["destination"].lower() == destination.lower():
                return route["frequency"]
        
        return "daily"
    
    @classmethod
    def is_route_available(cls, provider_code: str, origin: str, destination: str) -> bool:
        """Check if a route is available for a provider."""
        provider = cls.TRANSPORT_PROVIDERS.get(provider_code)
        if not provider:
            return False
        
        for route in provider["routes"]:
            if route["origin"].lower() == origin.lower() and route["destination"].lower() == destination.lower():
                return True
        
        return False
    
    @classmethod
    def get_provider_coverage(cls, provider_code: str) -> List[str]:
        """Get coverage zones for a provider."""
        provider = cls.TRANSPORT_PROVIDERS.get(provider_code)
        if not provider:
            return []
        return provider["coverage"]
    
    @classmethod
    def get_all_cities(cls) -> List[str]:
        """Get all available cities."""
        return list(cls.CITIES.keys())
    
    @classmethod
    def get_cities_by_zone(cls, zone: str) -> List[str]:
        """Get cities in a specific zone."""
        return [city for city, data in cls.CITIES.items() if data["zone"] == zone]
    
    @classmethod
    def get_available_providers_for_route(cls, origin: str, destination: str) -> List[str]:
        """Get providers that serve a specific route."""
        available_providers = []
        for code, provider in cls.TRANSPORT_PROVIDERS.items():
            if cls.is_route_available(code, origin, destination):
                available_providers.append(code)
        return available_providers
