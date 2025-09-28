from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_db
from ..services.payment_service import PaymentService
from ..services.booking_service import BookingService
from .auth import get_current_user

router = APIRouter()


# Pydantic models
class PaymentInitializeRequest(BaseModel):
    booking_id: str
    payment_method: str = "card"
    provider: str = "paystack"


class PaymentInitializeResponse(BaseModel):
    payment_reference: str
    status: str
    amount: float
    currency: str
    payment_method: str
    provider: str
    authorization_url: str
    access_code: str
    expires_at: float


class PaymentVerificationResponse(BaseModel):
    payment_reference: str
    status: str
    amount: float
    currency: str
    provider: str
    transaction_id: Optional[str] = None
    gateway_response: str
    paid_at: Optional[str] = None
    message: str


class RefundRequest(BaseModel):
    amount: Optional[float] = None
    reason: str = "Customer request"


class RefundResponse(BaseModel):
    refund_reference: str
    status: str
    amount: float
    currency: str
    booking_reference: str
    reason: str
    processed_at: Optional[str] = None
    message: str


class PaymentMethodResponse(BaseModel):
    method: str
    name: str
    provider: str
    currency: str


class BookingTotalResponse(BaseModel):
    base_amount: float
    booking_fee: float
    platform_fee: float
    insurance_fee: float
    wifi_fee: float
    total_fees: float
    grand_total: float
    breakdown: dict


@router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    payment_request: PaymentInitializeRequest,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Initialize payment for a booking."""
    try:
        # Determine user email: prefer authenticated user; fallback to guest email from booking
        user_email = current_user["email"] if current_user else None
        if not user_email:
            booking_details = await BookingService.get_booking_details(session, payment_request.booking_id)
            if not booking_details or not booking_details.get("guest_email"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User email is required for payment"
                )
            user_email = booking_details["guest_email"]

        # Calculate accurate amount for the booking
        totals = await PaymentService.calculate_booking_total(session, payment_request.booking_id)
        amount = totals.get("grand_total")

        payment_data = await PaymentService.initialize_payment(
            session=session,
            booking_id=payment_request.booking_id,
            amount=amount,
            user_email=user_email,
            payment_method=payment_request.payment_method,
            provider=payment_request.provider
        )
        
        return PaymentInitializeResponse(**payment_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize payment"
        )


@router.post("/verify/{payment_reference}", response_model=PaymentVerificationResponse)
async def verify_payment(
    payment_reference: str,
    provider: str = Query("paystack", description="Payment provider"),
    session: AsyncSession = Depends(get_db)
):
    """Verify payment status."""
    try:
        verification_data = await PaymentService.verify_payment(
            session=session,
            payment_reference=payment_reference,
            provider=provider
        )
        
        return PaymentVerificationResponse(**verification_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment"
        )


@router.post("/refund/{booking_id}", response_model=RefundResponse)
async def process_refund(
    booking_id: str,
    refund_request: RefundRequest,
    current_user: Optional[dict] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Process refund for a booking."""
    try:
        refund_data = await PaymentService.process_refund(
            session=session,
            booking_id=booking_id,
            amount=refund_request.amount,
            reason=refund_request.reason
        )
        
        return RefundResponse(**refund_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )


@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    provider: str = Query("paystack", description="Payment provider")
):
    """Get available payment methods."""
    try:
        methods = await PaymentService.get_payment_methods(provider=provider)
        return [PaymentMethodResponse(**method) for method in methods]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/booking/{booking_id}/total", response_model=BookingTotalResponse)
async def calculate_booking_total(
    booking_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Calculate total amount for a booking including fees."""
    try:
        total_data = await PaymentService.calculate_booking_total(
            session=session,
            booking_id=booking_id
        )
        
        return BookingTotalResponse(**total_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate booking total"
        )


@router.get("/statistics")
async def get_payment_statistics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get payment statistics (admin only)."""
    # Check if user is admin
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        stats = await PaymentService.get_payment_statistics(session)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment statistics"
        )


# Webhook endpoints for payment providers
@router.post("/webhook/paystack")
async def paystack_webhook(
    request_data: dict,
    session: AsyncSession = Depends(get_db)
):
    """Handle Paystack webhook notifications."""
    # This would contain the actual webhook processing logic
    # For now, we'll just acknowledge the webhook
    return {"status": "received", "message": "Webhook processed"}


@router.post("/webhook/flutterwave")
async def flutterwave_webhook(
    request_data: dict,
    session: AsyncSession = Depends(get_db)
):
    """Handle Flutterwave webhook notifications."""
    # This would contain the actual webhook processing logic
    # For now, we'll just acknowledge the webhook
    return {"status": "received", "message": "Webhook processed"}
