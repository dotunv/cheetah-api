import uuid
import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database.models import WifiCode, Booking, WifiUsageStatus
from ..database.config import get_settings
from sqlalchemy import func

_settings = get_settings()


class WifiService:
    """Service for managing WiFi codes and integrations."""
    
    @staticmethod
    def generate_wifi_code() -> str:
        """Generate a unique WiFi code."""
        # Generate a 8-character alphanumeric code
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(8))
    
    @staticmethod
    def generate_qr_code_data(wifi_code: str) -> str:
        """Generate QR code data for WiFi code."""
        # In a real implementation, this would generate actual QR code data
        # For now, we'll return a simple data string
        return f"WIFI:T:WPA;S:CheetahWiFi;P:{wifi_code};;"
    
    @staticmethod
    async def mock_generate_code(duration_minutes: int = 480) -> Dict[str, Any]:
        """Mock API call to generate WiFi code with provider."""
        # Simulate API delay
        import asyncio
        if _settings.DEBUG:
            await asyncio.sleep(0.05)
        
        # Generate mock WiFi code
        wifi_code = WifiService.generate_wifi_code()
        expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        return {
            "success": True,
            "code": wifi_code,
            "provider_code_id": f"WIFI_{wifi_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "expiry_time": expiry_time,
            "bandwidth_limit_mb": 500,
            "message": "WiFi code generated successfully"
        }
    
    @staticmethod
    async def generate_wifi_code_for_booking(
        session: AsyncSession,
        booking_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Generate WiFi code for a specific booking."""
        try:
            # Get booking details
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            
            if not booking:
                return None
            
            # Calculate WiFi duration based on trip duration
            # For now, we'll use a default duration of 8 hours
            wifi_duration_minutes = 480  # 8 hours
            
            # Call WiFi provider API
            wifi_response = await WifiService.mock_generate_code(wifi_duration_minutes)
            
            if not wifi_response["success"]:
                return None
            
            # Generate QR code data
            qr_code_data = WifiService.generate_qr_code_data(wifi_response["code"])
            
            # Create WiFi code record
            wifi_code = WifiCode(
                booking_id=booking_id,
                code=wifi_response["code"],
                qr_code_data=qr_code_data,
                expiry_time=wifi_response["expiry_time"],
                usage_status=WifiUsageStatus.UNUSED,
                bandwidth_limit_mb=wifi_response["bandwidth_limit_mb"],
                provider_code_id=wifi_response["provider_code_id"]
            )
            
            session.add(wifi_code)
            await session.commit()
            await session.refresh(wifi_code)
            
            return {
                "id": str(wifi_code.id),
                "code": wifi_code.code,
                "qr_code_data": wifi_code.qr_code_data,
                "expiry_time": wifi_code.expiry_time.isoformat(),
                "usage_status": wifi_code.usage_status.value,
                "bandwidth_limit_mb": wifi_code.bandwidth_limit_mb
            }
            
        except Exception as e:
            print(f"Error generating WiFi code for booking {booking_id}: {e}")
            return None
    
    @staticmethod
    async def get_wifi_code_by_id(
        session: AsyncSession,
        wifi_code_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get WiFi code by ID."""
        result = await session.execute(
            select(WifiCode).where(WifiCode.id == uuid.UUID(wifi_code_id))
        )
        wifi_code = result.scalar_one_or_none()
        
        if not wifi_code:
            return None
        
        return {
            "id": str(wifi_code.id),
            "booking_id": str(wifi_code.booking_id),
            "code": wifi_code.code,
            "qr_code_data": wifi_code.qr_code_data,
            "expiry_time": wifi_code.expiry_time.isoformat(),
            "usage_status": wifi_code.usage_status.value,
            "bandwidth_limit_mb": wifi_code.bandwidth_limit_mb,
            "provider_code_id": wifi_code.provider_code_id,
            "created_at": wifi_code.created_at.isoformat(),
            "updated_at": wifi_code.updated_at.isoformat()
        }
    
    @staticmethod
    async def get_booking_wifi_code(
        session: AsyncSession,
        booking_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get WiFi code for a specific booking."""
        result = await session.execute(
            select(WifiCode).where(WifiCode.booking_id == uuid.UUID(booking_id))
        )
        wifi_code = result.scalar_one_or_none()
        
        if not wifi_code:
            return None
        
        return await WifiService.get_wifi_code_by_id(session, str(wifi_code.id))
    
    @staticmethod
    async def get_user_wifi_codes(
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all WiFi codes for a user through their bookings."""
        # Get WiFi codes through bookings
        query = (
            select(WifiCode)
            .join(Booking, WifiCode.booking_id == Booking.id)
            .where(Booking.user_id == uuid.UUID(user_id))
            .order_by(WifiCode.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(query)
        wifi_codes = result.scalars().all()

        return [
            {
                "id": str(w.id),
                "booking_id": str(w.booking_id),
                "code": w.code,
                "qr_code_data": w.qr_code_data,
                "expiry_time": w.expiry_time.isoformat(),
                "usage_status": w.usage_status.value,
                "bandwidth_limit_mb": w.bandwidth_limit_mb,
                "provider_code_id": w.provider_code_id,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
            }
            for w in wifi_codes
        ]
    
    @staticmethod
    async def get_active_wifi_codes(
        session: AsyncSession,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active WiFi codes."""
        query = select(WifiCode).where(
            and_(
                WifiCode.usage_status == WifiUsageStatus.UNUSED,
                WifiCode.expiry_time > datetime.now(timezone.utc)
            )
        )
        
        if user_id:
            query = (
                query.join(Booking, WifiCode.booking_id == Booking.id)
                .where(Booking.user_id == uuid.UUID(user_id))
            )
        
        query = query.order_by(WifiCode.created_at.desc())
        
        result = await session.execute(query)
        wifi_codes = result.scalars().all()

        return [
            {
                "id": str(w.id),
                "booking_id": str(w.booking_id),
                "code": w.code,
                "qr_code_data": w.qr_code_data,
                "expiry_time": w.expiry_time.isoformat(),
                "usage_status": w.usage_status.value,
                "bandwidth_limit_mb": w.bandwidth_limit_mb,
                "provider_code_id": w.provider_code_id,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
            }
            for w in wifi_codes
        ]
    
    @staticmethod
    async def use_wifi_code(
        session: AsyncSession,
        wifi_code_id: str
    ) -> bool:
        """Mark WiFi code as used."""
        result = await session.execute(
            select(WifiCode).where(WifiCode.id == uuid.UUID(wifi_code_id))
        )
        wifi_code = result.scalar_one_or_none()
        
        if not wifi_code:
            return False
        
        # Check if code is still valid
        if wifi_code.usage_status != WifiUsageStatus.UNUSED:
            return False
        
        if wifi_code.expiry_time <= datetime.now(timezone.utc):
            return False
        
        # Mark as used
        wifi_code.usage_status = WifiUsageStatus.USED
        wifi_code.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True
    
    @staticmethod
    async def validate_wifi_code(
        session: AsyncSession,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """Validate a WiFi code."""
        result = await session.execute(
            select(WifiCode).where(WifiCode.code == code)
        )
        wifi_code = result.scalar_one_or_none()
        
        if not wifi_code:
            return None
        
        # Check if code is valid
        if wifi_code.usage_status != WifiUsageStatus.UNUSED:
            return {
                "valid": False,
                "message": "WiFi code has already been used"
            }
        
        if wifi_code.expiry_time <= datetime.now(timezone.utc):
            return {
                "valid": False,
                "message": "WiFi code has expired"
            }
        
        return {
            "valid": True,
            "wifi_code_id": str(wifi_code.id),
            "bandwidth_limit_mb": wifi_code.bandwidth_limit_mb,
            "expiry_time": wifi_code.expiry_time.isoformat()
        }
    
    @staticmethod
    async def get_wifi_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Get WiFi usage statistics."""
        # Total WiFi codes
        total_codes = (
            await session.execute(select(func.count(WifiCode.id)))
        ).scalar_one()

        # Active WiFi codes
        active_codes = (
            await session.execute(
                select(func.count(WifiCode.id)).where(
                    and_(
                        WifiCode.usage_status == WifiUsageStatus.UNUSED,
                        WifiCode.expiry_time > datetime.now(timezone.utc)
                    )
                )
            )
        ).scalar_one()

        # Used WiFi codes
        used_codes = (
            await session.execute(
                select(func.count(WifiCode.id)).where(WifiCode.usage_status == WifiUsageStatus.USED)
            )
        ).scalar_one()

        # Expired WiFi codes
        expired_codes = (
            await session.execute(
                select(func.count(WifiCode.id)).where(
                    and_(
                        WifiCode.usage_status == WifiUsageStatus.UNUSED,
                        WifiCode.expiry_time <= datetime.now(timezone.utc)
                    )
                )
            )
        ).scalar_one()

        # Today's generated codes
        today = datetime.now().date()
        today_codes = (
            await session.execute(
                select(func.count(WifiCode.id)).where(
                    and_(
                        WifiCode.created_at >= today,
                        WifiCode.created_at < today + timedelta(days=1)
                    )
                )
            )
        ).scalar_one()
        
        return {
            "total_codes": total_codes,
            "active_codes": active_codes,
            "used_codes": used_codes,
            "expired_codes": expired_codes,
            "today_generated": today_codes
        }
    
    @staticmethod
    async def mock_wifi_usage_monitoring(
        wifi_code: str,
        usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock API call to monitor WiFi usage with provider."""
        # Simulate API delay
        import asyncio
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "wifi_code": wifi_code,
            "usage_mb": usage_data.get("usage_mb", 0),
            "remaining_mb": usage_data.get("remaining_mb", 500),
            "status": "active" if usage_data.get("remaining_mb", 500) > 0 else "exhausted"
        }
    
    @staticmethod
    async def generate_qr_code(wifi_code: str) -> str:
        """Generate QR code data for WiFi code."""
        return WifiService.generate_qr_code_data(wifi_code)
    
    @staticmethod
    async def activate_wifi_code(
        session: AsyncSession,
        code_id: str,
        device_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activate a WiFi code."""
        result = await session.execute(
            select(WifiCode).where(WifiCode.id == code_id)
        )
        wifi_code = result.scalar_one_or_none()
        
        if not wifi_code:
            return {
                "success": False,
                "message": "WiFi code not found"
            }
        
        # Check if code is still valid
        if wifi_code.expiry_time < datetime.now(timezone.utc):
            return {
                "success": False,
                "message": "WiFi code has expired"
            }
        
        if wifi_code.usage_status != WifiUsageStatus.UNUSED:
            return {
                "success": False,
                "message": "WiFi code has already been used"
            }
        
        # Mock activation
        return {
            "success": True,
            "message": "WiFi code activated successfully",
            "session_duration_minutes": 480,  # 8 hours
            "bandwidth_remaining_mb": wifi_code.bandwidth_limit_mb or 500
        }
    
    @staticmethod
    async def get_usage_stats(code_id: str) -> Dict[str, Any]:
        """Get usage statistics for a WiFi code."""
        # Mock usage statistics
        return {
            "total_usage_mb": random.randint(0, 200),
            "remaining_bandwidth_mb": random.randint(300, 500),
            "session_count": random.randint(1, 5),
            "last_used": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))).isoformat()
        } 