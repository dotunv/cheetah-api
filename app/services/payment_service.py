import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx
import json

from ..database.models import Booking, PaymentStatus, User, BookingStatus
from ..database.config import get_settings
from sqlalchemy import func

_settings = get_settings()
from ..database.config import get_settings


class PaymentService:
    """Service for handling payment processing and integrations."""
    
    # Mock payment providers for demo
    PAYMENT_PROVIDERS = {
        "paystack": {
            "name": "Paystack",
            "base_url": "https://api.paystack.co",
            "currency": "NGN",
            "supported_methods": ["card", "bank_transfer", "ussd", "qr"]
        },
        "flutterwave": {
            "name": "Flutterwave",
            "base_url": "https://api.flutterwave.com/v3",
            "currency": "NGN", 
            "supported_methods": ["card", "bank_transfer", "ussd", "mobile_money"]
        }
    }
    
    @staticmethod
    async def initialize_payment(
        session: AsyncSession,
        booking_id: str,
        amount: float,
        user_email: str,
        user_phone: Optional[str] = None,
        payment_method: str = "card",
        provider: str = "paystack"
    ) -> Dict[str, Any]:
        """Initialize payment for a booking."""
        # Get booking details
        result = await session.execute(
            select(Booking).where(Booking.id == uuid.UUID(booking_id))
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if booking.payment_status == PaymentStatus.PAID:
            raise ValueError("Booking already paid")
        
        # Mock payment initialization
        payment_data = await PaymentService.mock_initialize_payment(
            booking_id=booking_id,
            amount=amount,
            user_email=user_email,
            user_phone=user_phone,
            payment_method=payment_method,
            provider=provider
        )
        
        # Update booking with payment reference
        booking.provider_booking_reference = payment_data["payment_reference"]
        booking.payment_status = PaymentStatus.PENDING
        await session.commit()
        
        return payment_data
    
    @staticmethod
    async def verify_payment(
        session: AsyncSession,
        payment_reference: str,
        provider: str = "paystack"
    ) -> Dict[str, Any]:
        """Verify payment status."""
        # Mock payment verification
        verification_data = await PaymentService.mock_verify_payment(
            payment_reference=payment_reference,
            provider=provider
        )
        
        # Update booking status if payment successful
        if verification_data["status"] == "success":
            result = await session.execute(
                select(Booking).where(Booking.provider_booking_reference == payment_reference)
            )
            booking = result.scalar_one_or_none()
            
            if booking:
                booking.payment_status = PaymentStatus.PAID
                booking.booking_status = BookingStatus.CONFIRMED
                await session.commit()
        
        return verification_data
    
    @staticmethod
    async def process_refund(
        session: AsyncSession,
        booking_id: str,
        amount: Optional[float] = None,
        reason: str = "Customer request"
    ) -> Dict[str, Any]:
        """Process refund for a booking."""
        # Get booking details
        result = await session.execute(
            select(Booking).where(Booking.id == uuid.UUID(booking_id))
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise ValueError("Booking not found")
        
        if booking.payment_status != PaymentStatus.PAID:
            raise ValueError("Cannot refund unpaid booking")
        
        refund_amount = amount or booking.total_amount
        
        # Mock refund processing
        refund_data = await PaymentService.mock_process_refund(
            booking_reference=booking.booking_reference,
            amount=refund_amount,
            reason=reason
        )
        
        # Update booking status
        if refund_data["status"] == "success":
            booking.payment_status = PaymentStatus.REFUNDED
            await session.commit()
        
        return refund_data
    
    @staticmethod
    async def get_payment_methods(
        provider: str = "paystack"
    ) -> List[Dict[str, Any]]:
        """Get available payment methods for a provider."""
        if provider not in PaymentService.PAYMENT_PROVIDERS:
            raise ValueError(f"Unsupported payment provider: {provider}")
        
        provider_info = PaymentService.PAYMENT_PROVIDERS[provider]
        
        payment_methods = []
        for method in provider_info["supported_methods"]:
            payment_methods.append({
                "method": method,
                "name": method.replace("_", " ").title(),
                "provider": provider,
                "currency": provider_info["currency"]
            })
        
        return payment_methods
    
    @staticmethod
    async def calculate_booking_total(
        session: AsyncSession,
        booking_id: str
    ) -> Dict[str, Any]:
        """Calculate total amount for booking including fees."""
        result = await session.execute(
            select(Booking).where(Booking.id == uuid.UUID(booking_id))
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise ValueError("Booking not found")
        
        # The booking.total_amount is already the computed total during booking creation.
        # To avoid double-counting, we treat booking.total_amount as the grand total here
        # and set fee components to zero. If fee breakdown is needed, compute it at booking time
        # and persist it separately.
        base_amount = booking.total_amount
        booking_fee = 0
        platform_fee = 0
        insurance_fee = 0
        wifi_fee = 0
        total_fees = 0
        grand_total = booking.total_amount
        
        return {
            "base_amount": base_amount,
            "booking_fee": booking_fee,
            "platform_fee": platform_fee,
            "insurance_fee": insurance_fee,
            "wifi_fee": wifi_fee,
            "total_fees": total_fees,
            "grand_total": grand_total,
            "breakdown": {
                "transport": base_amount,
                "fees": total_fees,
                "total": grand_total
            }
        }
    
    # Mock implementations for demo
    @staticmethod
    async def mock_initialize_payment(
        booking_id: str,
        amount: float,
        user_email: str,
        user_phone: Optional[str] = None,
        payment_method: str = "card",
        provider: str = "paystack"
    ) -> Dict[str, Any]:
        """Mock payment initialization."""
        payment_reference = f"{provider.upper()}_{str(uuid.uuid4())[:12]}"
        
        return {
            "payment_reference": payment_reference,
            "status": "pending",
            "amount": amount,
            "currency": "NGN",
            "payment_method": payment_method,
            "provider": provider,
            "authorization_url": f"https://checkout.{provider}.com/pay/{payment_reference}",
            "access_code": str(uuid.uuid4()),
            "expires_at": (datetime.now(timezone.utc).timestamp() + 3600),  # 1 hour
            "user_email": user_email,
            "user_phone": user_phone
        }
    
    @staticmethod
    async def mock_verify_payment(
        payment_reference: str,
        provider: str = "paystack"
    ) -> Dict[str, Any]:
        """Mock payment verification."""
        # Simulate API call delay
        import asyncio
        if _settings.DEBUG:
            await asyncio.sleep(0.05)
        
        # Mock verification result (80% success rate for demo)
        import random
        is_successful = random.random() > 0.2
        
        return {
            "payment_reference": payment_reference,
            "status": "success" if is_successful else "failed",
            "amount": 8000 if is_successful else 0,
            "currency": "NGN",
            "provider": provider,
            "transaction_id": f"TXN_{str(uuid.uuid4())[:8]}" if is_successful else None,
            "gateway_response": "Approved" if is_successful else "Declined",
            "paid_at": datetime.now(timezone.utc).isoformat() if is_successful else None,
            "message": "Payment successful" if is_successful else "Payment failed"
        }
    
    @staticmethod
    async def mock_process_refund(
        booking_reference: str,
        amount: float,
        reason: str
    ) -> Dict[str, Any]:
        """Mock refund processing."""
        import asyncio
        if _settings.DEBUG:
            await asyncio.sleep(0.05)
        
        import random
        is_successful = random.random() > 0.1  # 90% success rate
        
        return {
            "refund_reference": f"REF_{str(uuid.uuid4())[:8]}",
            "status": "success" if is_successful else "failed",
            "amount": amount if is_successful else 0,
            "currency": "NGN",
            "booking_reference": booking_reference,
            "reason": reason,
            "processed_at": datetime.now(timezone.utc).isoformat() if is_successful else None,
            "message": "Refund processed successfully" if is_successful else "Refund failed"
        }
    
    @staticmethod
    async def get_payment_statistics(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get payment statistics."""
        # Total payments
        total_payments = (
            await session.execute(
                select(func.count(Booking.id)).where(Booking.payment_status == PaymentStatus.PAID)
            )
        ).scalar_one()

        # Total revenue
        total_revenue = (
            await session.execute(
                select(func.coalesce(func.sum(Booking.total_amount), 0.0)).where(Booking.payment_status == PaymentStatus.PAID)
            )
        ).scalar_one()

        # Pending payments
        pending_payments = (
            await session.execute(
                select(func.count(Booking.id)).where(Booking.payment_status == PaymentStatus.PENDING)
            )
        ).scalar_one()

        # Failed payments
        failed_payments = (
            await session.execute(
                select(func.count(Booking.id)).where(Booking.payment_status == PaymentStatus.FAILED)
            )
        ).scalar_one()
        
        return {
            "total_payments": total_payments,
            "total_revenue": float(total_revenue),
            "pending_payments": pending_payments,
            "failed_payments": failed_payments,
            "success_rate": (total_payments / (total_payments + failed_payments) * 100) if (total_payments + failed_payments) > 0 else 0
        }
