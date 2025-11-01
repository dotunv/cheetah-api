import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import BackgroundTasks

from ..database.models import (
    Booking, Schedule, User, BookingStatus, PaymentStatus, 
    InsurancePolicy, WifiCode, InsuranceStatus, WifiUsageStatus
)
from ..services.transport_provider_service import TransportProviderService
from ..services.insurance_service import InsuranceService
from ..services.wifi_service import WifiService
from ..services.notification_service import NotificationService


class BookingService:
    """Service for managing bookings and related operations."""
    
    @staticmethod
    def generate_booking_reference() -> str:
        """Generate a unique booking reference."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"CHT{timestamp}{random_suffix}"
    
    @staticmethod
    async def search_routes(
        session: AsyncSession,
        origin: str,
        destination: str,
        date: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for available routes across all providers."""
        return await TransportProviderService.search_routes(
            session, origin, destination, date, filters
        )
    
    @staticmethod
    async def get_schedule_details(
        session: AsyncSession,
        schedule_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific schedule."""
        # For now, we'll get this from the transport provider service
        # In a real implementation, this would query the database
        provider_code = schedule_id.split("_")[0]
        
        # Mock schedule details - in a real implementation, this would come from the database
        schedule_details = {
            "schedule_id": schedule_id,
            "provider_code": provider_code,
            "origin": "Lagos",  # This would come from the actual schedule
            "destination": "Abuja",  # This would come from the actual schedule
            "departure_time": datetime.now() + timedelta(days=1),
            "arrival_time": datetime.now() + timedelta(days=1, hours=12),
            "duration_minutes": 720,
            "total_seats": 30,
            "available_seats": 15,
            "base_price": 8000,
            "vehicle_type": "Luxury Bus",
            "amenities": ["AC", "WiFi", "USB Charging", "Reclining Seats"]
        }
        
        return schedule_details
    
    @staticmethod
    async def create_booking(
        session: AsyncSession,
        schedule_id: str,
        passenger_details: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        guest_email: Optional[str] = None,
        guest_phone: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Create a new booking."""
        # Validate passenger details
        if not passenger_details:
            raise ValueError("At least one passenger is required")
        
        # Get schedule details
        schedule_details = await BookingService.get_schedule_details(session, schedule_id)
        if not schedule_details:
            raise ValueError("Schedule not found")
        
        # Check seat availability
        if len(passenger_details) > schedule_details["available_seats"]:
            raise ValueError(f"Only {schedule_details['available_seats']} seats available")
        
        # Calculate total amount
        total_amount = schedule_details["base_price"] * len(passenger_details)
        booking_fee = 200
        grand_total = total_amount + booking_fee
        
        # For now, we'll use a mock UUID for the schedule_id since we're using string-based IDs
        # In a real implementation, you would look up the actual schedule UUID from the database
        # based on the schedule_code or create a mapping
        mock_schedule_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, schedule_id)
        
        # Create booking record
        booking = Booking(
            booking_reference=BookingService.generate_booking_reference(),
            user_id=uuid.UUID(user_id) if user_id else None,
            guest_email=guest_email,
            guest_phone=guest_phone,
            schedule_id=mock_schedule_uuid,  # Use generated UUID based on schedule_id string
            passenger_count=len(passenger_details),
            total_amount=grand_total,
            booking_status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            passenger_details=json.dumps(passenger_details),
            notes="Booking created via Cheetah API"
        )
        
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        
        # Book with transport provider
        provider_code = schedule_details["provider_code"]
        provider_booking = await TransportProviderService.mock_book_ticket(
            provider_code=provider_code,
            schedule_id=schedule_id,
            passenger_details=passenger_details,
            contact_email=guest_email or (await BookingService.get_user_email(session, user_id)),
            contact_phone=guest_phone
        )
        
        if provider_booking["success"]:
            # Update booking with provider reference
            booking.provider_booking_reference = provider_booking["provider_booking_reference"]
            booking.booking_status = BookingStatus.CONFIRMED
            booking.payment_status = PaymentStatus.PAID  # Assuming payment is handled separately
            await session.commit()
            
            # Add background tasks for insurance and WiFi
            if background_tasks:
                background_tasks.add_task(
                    BookingService._generate_insurance_policy,
                    session,
                    booking.id,
                    passenger_details
                )
                background_tasks.add_task(
                    BookingService._generate_wifi_code,
                    session,
                    booking.id
                )
                background_tasks.add_task(
                    BookingService._send_booking_confirmation,
                    booking.id,
                    guest_email or (await BookingService.get_user_email(session, user_id))
                )
        
        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "provider_booking_reference": booking.provider_booking_reference,
            "total_amount": booking.total_amount,
            "booking_status": booking.booking_status.value,
            "payment_status": booking.payment_status.value,
            "passenger_count": booking.passenger_count,
            "schedule_details": schedule_details
        }
    
    @staticmethod
    async def get_booking_details(
        session: AsyncSession,
        booking_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed booking information."""
        result = await session.execute(
            select(Booking).where(Booking.id == uuid.UUID(booking_id))
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            return None
        
        # Get related data
        insurance_policy = None
        wifi_code = None
        
        if booking.insurance_policy:
            insurance_policy = {
                "id": str(booking.insurance_policy.id),
                "policy_number": booking.insurance_policy.policy_number,
                "status": booking.insurance_policy.status.value,
                "coverage_amount": booking.insurance_policy.coverage_amount,
                "start_date": booking.insurance_policy.start_date.isoformat(),
                "end_date": booking.insurance_policy.end_date.isoformat()
            }
        
        if booking.wifi_code:
            wifi_code = {
                "id": str(booking.wifi_code.id),
                "code": booking.wifi_code.code,
                "qr_code_data": booking.wifi_code.qr_code_data,
                "expiry_time": booking.wifi_code.expiry_time.isoformat(),
                "usage_status": booking.wifi_code.usage_status.value,
                "bandwidth_limit_mb": booking.wifi_code.bandwidth_limit_mb
            }
        
        return {
            "id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "user_id": str(booking.user_id) if booking.user_id else None,
            "guest_email": booking.guest_email,
            "guest_phone": booking.guest_phone,
            "schedule_id": str(booking.schedule_id) if booking.schedule_id else None,
            "passenger_count": booking.passenger_count,
            "total_amount": booking.total_amount,
            "booking_status": booking.booking_status.value,
            "payment_status": booking.payment_status.value,
            "passenger_details": json.loads(booking.passenger_details),
            "provider_booking_reference": booking.provider_booking_reference,
            "notes": booking.notes,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat(),
            "insurance_policy": insurance_policy,
            "wifi_code": wifi_code
        }

    @staticmethod
    async def get_booking_by_reference(
        session: AsyncSession,
        booking_reference: str
    ) -> Optional[Dict[str, Any]]:
        """Get booking details by booking reference."""
        result = await session.execute(
            select(Booking).where(Booking.booking_reference == booking_reference)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            return None
        # Reuse get_booking_details to ensure consistent shape
        return await BookingService.get_booking_details(session, str(booking.id))
    
    @staticmethod
    async def get_user_bookings(
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[BookingStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get bookings for a specific user."""
        query = select(Booking).where(Booking.user_id == uuid.UUID(user_id))
        
        if status:
            query = query.where(Booking.booking_status == status)
        
        query = query.order_by(Booking.created_at.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        bookings = result.scalars().all()
        
        booking_list = []
        for booking in bookings:
            booking_data = await BookingService.get_booking_details(session, str(booking.id))
            if booking_data:
                booking_list.append(booking_data)
        
        return booking_list

    @staticmethod
    async def get_guest_bookings(
        session: AsyncSession,
        guest_email: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[BookingStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get bookings for a specific guest email."""
        query = select(Booking).where(Booking.guest_email == guest_email)
        
        if status:
            query = query.where(Booking.booking_status == status)
        
        query = query.order_by(Booking.created_at.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        bookings = result.scalars().all()
        
        booking_list = []
        for booking in bookings:
            booking_data = await BookingService.get_booking_details(session, str(booking.id))
            if booking_data:
                booking_list.append(booking_data)
        
        return booking_list

    @staticmethod
    async def get_all_bookings(
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        status: Optional[BookingStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get all bookings with optional status filter."""
        query = select(Booking)
        if status:
            query = query.where(Booking.booking_status == status)
        query = query.order_by(Booking.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        bookings = result.scalars().all()

        booking_list: List[Dict[str, Any]] = []
        for booking in bookings:
            details = await BookingService.get_booking_details(session, str(booking.id))
            if details:
                booking_list.append(details)
        return booking_list
    
    @staticmethod
    async def cancel_booking(
        session: AsyncSession,
        booking_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Cancel a booking."""
        result = await session.execute(
            select(Booking).where(Booking.id == uuid.UUID(booking_id))
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            return False
        
        # Check if user has permission to cancel
        if user_id and str(booking.user_id) != user_id:
            return False
        
        # Check if booking can be cancelled
        if booking.booking_status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            return False
        # Disallow cancelling a paid booking without a refund flow
        if booking.payment_status == PaymentStatus.PAID:
            return False
        
        # Update booking status
        booking.booking_status = BookingStatus.CANCELLED
        booking.updated_at = datetime.now(timezone.utc)
        
        # Cancel insurance policy if exists
        if booking.insurance_policy:
        booking.insurance_policy.status = InsuranceStatus.CANCELLED
        booking.insurance_policy.updated_at = datetime.now(timezone.utc)
        
        # Cancel WiFi code if exists
        if booking.wifi_code:
        booking.wifi_code.usage_status = WifiUsageStatus.EXPIRED
        booking.wifi_code.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True

    @staticmethod
    async def confirm_booking(
        session: AsyncSession,
        booking_id: str
    ) -> bool:
        """Confirm a booking (admin action)."""
        result = await session.execute(
            select(Booking).where(Booking.id == uuid.UUID(booking_id))
        )
        booking = result.scalar_one_or_none()
        if not booking:
            return False

        # If already cancelled or completed, cannot confirm
        if booking.booking_status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            return False
        # Require payment to be completed before confirming
        if booking.payment_status != PaymentStatus.PAID:
            return False

        booking.booking_status = BookingStatus.CONFIRMED
        booking.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return True
    
    @staticmethod
    async def _generate_insurance_policy(
        session: AsyncSession,
        booking_id: uuid.UUID,
        passenger_details: List[Dict[str, Any]]
    ):
        """Generate insurance policy for booking (background task)."""
        try:
            # Get booking details
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            
            if not booking:
                return
            
            # Generate insurance policy
            insurance_data = await InsuranceService.auto_enroll_for_booking(
                session, booking_id, passenger_details
            )
            
            if insurance_data:
                print(f"Insurance policy generated for booking {booking_id}: {insurance_data['policy_number']}")
            
        except Exception as e:
            print(f"Error generating insurance policy for booking {booking_id}: {e}")
    
    @staticmethod
    async def _generate_wifi_code(
        session: AsyncSession,
        booking_id: uuid.UUID
    ):
        """Generate WiFi code for booking (background task)."""
        try:
            wifi_data = await WifiService.generate_wifi_code_for_booking(session, booking_id)
            
            if wifi_data:
                print(f"WiFi code generated for booking {booking_id}: {wifi_data['code']}")
            
        except Exception as e:
            print(f"Error generating WiFi code for booking {booking_id}: {e}")
    
    @staticmethod
    async def _send_booking_confirmation(
        booking_id: uuid.UUID,
        email: str
    ):
        """Send booking confirmation email (background task)."""
        try:
            await NotificationService.send_booking_confirmation(email, booking_id)
            print(f"Booking confirmation sent to {email} for booking {booking_id}")
            
        except Exception as e:
            print(f"Error sending booking confirmation for booking {booking_id}: {e}")
    
    @staticmethod
    async def get_user_email(session: AsyncSession, user_id: str) -> Optional[str]:
        """Get user email by user ID."""
        if not user_id:
            return None
        
        result = await session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        return user.email if user else None
    
    @staticmethod
    async def get_booking_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Get booking statistics."""
        # Total bookings
        total_bookings_result = await session.execute(select(Booking))
        total_bookings = len(total_bookings_result.scalars().all())
        
        # Confirmed bookings
        confirmed_bookings_result = await session.execute(
            select(Booking).where(Booking.booking_status == BookingStatus.CONFIRMED)
        )
        confirmed_bookings = len(confirmed_bookings_result.scalars().all())
        
        # Total revenue
        revenue_result = await session.execute(
            select(Booking).where(Booking.payment_status == PaymentStatus.PAID)
        )
        paid_bookings = revenue_result.scalars().all()
        total_revenue = sum(booking.total_amount for booking in paid_bookings)
        
        # Today's bookings
        today = datetime.now().date()
        today_bookings_result = await session.execute(
            select(Booking).where(
                and_(
                    Booking.created_at >= today,
                    Booking.created_at < today + timedelta(days=1)
                )
            )
        )
        today_bookings = len(today_bookings_result.scalars().all())
        
        return {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "total_revenue": float(total_revenue),
            "today_bookings": today_bookings
        } 