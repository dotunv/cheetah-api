from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import uuid

from ..database.models import User, Booking, InsurancePolicy, WifiCode, BookingStatus, PaymentStatus
from .auth_service import AuthService


class UserService:
    """User service for user-related business logic."""
    
    @staticmethod
    async def get_user_profile(session: AsyncSession, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get user profile with statistics."""
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            return None
        
        # Get user statistics
        stats = await UserService.get_user_statistics(session, user_id)
        
        return {
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "statistics": stats
        }
    
    @staticmethod
    async def update_user_profile(
        session: AsyncSession,
        user_id: uuid.UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[User]:
        """Update user profile information."""
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            return None
        
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        
        user.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_bookings(
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[BookingStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get user's booking history."""
        query = select(Booking).where(Booking.user_id == user_id)
        
        if status:
            query = query.where(Booking.booking_status == status)
        
        query = query.order_by(Booking.created_at.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        bookings = result.scalars().all()
        
        booking_list = []
        for booking in bookings:
            booking_data = {
                "id": str(booking.id),
                "booking_reference": booking.booking_reference,
                "schedule_id": str(booking.schedule_id),
                "passenger_count": booking.passenger_count,
                "total_amount": booking.total_amount,
                "booking_status": booking.booking_status.value,
                "payment_status": booking.payment_status.value,
                "created_at": booking.created_at.isoformat(),
                "provider_booking_reference": booking.provider_booking_reference,
                "notes": booking.notes
            }
            booking_list.append(booking_data)
        
        return booking_list
    
    @staticmethod
    async def get_user_insurance_policies(
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's insurance policies."""
        query = (
            select(InsurancePolicy)
            .where(InsurancePolicy.user_id == user_id)
            .order_by(InsurancePolicy.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(query)
        policies = result.scalars().all()
        
        policy_list = []
        for policy in policies:
            policy_data = {
                "id": str(policy.id),
                "booking_id": str(policy.booking_id),
                "policy_number": policy.policy_number,
                "coverage_details_url": policy.coverage_details_url,
                "status": policy.status.value,
                "start_date": policy.start_date.isoformat(),
                "end_date": policy.end_date.isoformat(),
                "coverage_amount": policy.coverage_amount,
                "created_at": policy.created_at.isoformat()
            }
            policy_list.append(policy_data)
        
        return policy_list
    
    @staticmethod
    async def get_user_wifi_codes(
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's WiFi codes."""
        # Get WiFi codes through bookings
        query = (
            select(WifiCode)
            .join(Booking, WifiCode.booking_id == Booking.id)
            .where(Booking.user_id == user_id)
            .order_by(WifiCode.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(query)
        wifi_codes = result.scalars().all()
        
        wifi_list = []
        for wifi in wifi_codes:
            wifi_data = {
                "id": str(wifi.id),
                "booking_id": str(wifi.booking_id),
                "code": wifi.code,
                "qr_code_data": wifi.qr_code_data,
                "expiry_time": wifi.expiry_time.isoformat(),
                "usage_status": wifi.usage_status.value,
                "bandwidth_limit_mb": wifi.bandwidth_limit_mb,
                "created_at": wifi.created_at.isoformat()
            }
            wifi_list.append(wifi_data)
        
        return wifi_list
    
    @staticmethod
    async def get_user_statistics(session: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user statistics."""
        # Total bookings
        total_bookings_result = await session.execute(
            select(func.count(Booking.id)).where(Booking.user_id == user_id)
        )
        total_bookings = total_bookings_result.scalar() or 0
        
        # Confirmed bookings
        confirmed_bookings_result = await session.execute(
            select(func.count(Booking.id)).where(
                and_(Booking.user_id == user_id, Booking.booking_status == BookingStatus.CONFIRMED)
            )
        )
        confirmed_bookings = confirmed_bookings_result.scalar() or 0
        
        # Total spent
        total_spent_result = await session.execute(
            select(func.sum(Booking.total_amount)).where(
                and_(Booking.user_id == user_id, Booking.payment_status == PaymentStatus.PAID)
            )
        )
        total_spent = total_spent_result.scalar() or 0.0
        
        # Active insurance policies
        active_policies_result = await session.execute(
            select(func.count(InsurancePolicy.id)).where(
                and_(
                    InsurancePolicy.user_id == user_id,
                    InsurancePolicy.status == "active",
                    InsurancePolicy.end_date > datetime.utcnow()
                )
            )
        )
        active_policies = active_policies_result.scalar() or 0
        
        # Active WiFi codes
        active_wifi_result = await session.execute(
            select(func.count(WifiCode.id))
            .join(Booking, WifiCode.booking_id == Booking.id)
            .where(
                and_(
                    Booking.user_id == user_id,
                    WifiCode.usage_status == "unused",
                    WifiCode.expiry_time > datetime.utcnow()
                )
            )
        )
        active_wifi = active_wifi_result.scalar() or 0
        
        return {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "total_spent": float(total_spent),
            "active_insurance_policies": active_policies,
            "active_wifi_codes": active_wifi
        }
    
    @staticmethod
    async def search_users(
        session: AsyncSession,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search users by various criteria (admin function)."""
        query = select(User)
        
        if email:
            query = query.where(User.email.ilike(f"%{email}%"))
        if phone:
            query = query.where(User.phone.ilike(f"%{phone}%"))
        if name:
            query = query.where(
                (User.first_name.ilike(f"%{name}%")) | (User.last_name.ilike(f"%{name}%"))
            )
        
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        user_list = []
        for user in users:
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "phone": user.phone,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat()
            }
            user_list.append(user_data)
        
        return user_list
    
    @staticmethod
    async def get_user_by_guest_email(session: AsyncSession, email: str) -> Optional[Dict[str, Any]]:
        """Get user by guest email (for guest bookings)."""
        # First try to find a registered user
        user = await AuthService.get_user_by_email(session, email)
        if user:
            return await UserService.get_user_profile(session, user.id)
        
        # If no registered user, get guest booking statistics
        guest_bookings_result = await session.execute(
            select(func.count(Booking.id)).where(Booking.guest_email == email)
        )
        guest_bookings = guest_bookings_result.scalar() or 0
        
        guest_spent_result = await session.execute(
            select(func.sum(Booking.total_amount)).where(
                and_(Booking.guest_email == email, Booking.payment_status == PaymentStatus.PAID)
            )
        )
        guest_spent = guest_spent_result.scalar() or 0.0
        
        return {
            "email": email,
            "is_guest": True,
            "statistics": {
                "total_bookings": guest_bookings,
                "total_spent": float(guest_spent)
            }
        }
