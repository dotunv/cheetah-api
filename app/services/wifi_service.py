import uuid
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database.models import WifiCode, Booking, WifiUsageStatus


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
        await asyncio.sleep(0.2)
        
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
        
        wifi_list = []
        for wifi_code in wifi_codes:
            wifi_data = await WifiService.get_wifi_code_by_id(session, str(wifi_code.id))
            if wifi_data:
                wifi_list.append(wifi_data)
        
        return wifi_list
    
    @staticmethod
    async def get_active_wifi_codes(
        session: AsyncSession,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active WiFi codes."""
        query = select(WifiCode).where(
            and_(
                WifiCode.usage_status == WifiUsageStatus.UNUSED,
                WifiCode.expiry_time > datetime.utcnow()
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
        
        wifi_list = []
        for wifi_code in wifi_codes:
            wifi_data = await WifiService.get_wifi_code_by_id(session, str(wifi_code.id))
            if wifi_data:
                wifi_list.append(wifi_data)
        
        return wifi_list
    
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
        
        if wifi_code.expiry_time <= datetime.utcnow():
            return False
        
        # Mark as used
        wifi_code.usage_status = WifiUsageStatus.USED
        wifi_code.updated_at = datetime.utcnow()
        
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
        
        if wifi_code.expiry_time <= datetime.utcnow():
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
        total_codes_result = await session.execute(select(WifiCode))
        total_codes = len(total_codes_result.scalars().all())
        
        # Active WiFi codes
        active_codes_result = await session.execute(
            select(WifiCode).where(
                and_(
                    WifiCode.usage_status == WifiUsageStatus.UNUSED,
                    WifiCode.expiry_time > datetime.utcnow()
                )
            )
        )
        active_codes = len(active_codes_result.scalars().all())
        
        # Used WiFi codes
        used_codes_result = await session.execute(
            select(WifiCode).where(WifiCode.usage_status == WifiUsageStatus.USED)
        )
        used_codes = len(used_codes_result.scalars().all())
        
        # Expired WiFi codes
        expired_codes_result = await session.execute(
            select(WifiCode).where(
                and_(
                    WifiCode.usage_status == WifiUsageStatus.UNUSED,
                    WifiCode.expiry_time <= datetime.utcnow()
                )
            )
        )
        expired_codes = len(expired_codes_result.scalars().all())
        
        # Today's generated codes
        today = datetime.now().date()
        today_codes_result = await session.execute(
            select(WifiCode).where(
                and_(
                    WifiCode.created_at >= today,
                    WifiCode.created_at < today + timedelta(days=1)
                )
            )
        )
        today_codes = len(today_codes_result.scalars().all())
        
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