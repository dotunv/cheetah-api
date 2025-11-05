import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_, func
from ..database.config import get_settings

_settings = get_settings()

from ..database.models import InsurancePolicy, Booking, User, InsuranceStatus


class InsuranceService:
    """Service for managing insurance policies and integrations."""
    
    @staticmethod
    def generate_policy_number() -> str:
        """Generate a unique insurance policy number."""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"INS{timestamp}{random_suffix}"
    
    @staticmethod
    async def mock_enroll_policy(
        passenger_details: List[Dict[str, Any]],
        booking_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock API call to enroll policy with insurance partner."""
        # Simulate API delay
        import asyncio
        if _settings.DEBUG:
            await asyncio.sleep(0.05)
        
        # Generate mock policy data
        policy_number = InsuranceService.generate_policy_number()
        coverage_amount = 1000000.0  # 1M Naira coverage
        
        # Calculate policy duration based on trip duration
        trip_duration_hours = booking_details.get("duration_hours", 12)
        policy_duration_hours = trip_duration_hours + 2  # Extra 2 hours for safety
        
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=policy_duration_hours)
        
        return {
            "success": True,
            "policy_number": policy_number,
            "provider_policy_id": f"PARTNER_{policy_number}",
            "coverage_amount": coverage_amount,
            "start_date": start_date,
            "end_date": end_date,
            "coverage_details_url": f"https://insurance-partner.com/policy/{policy_number}",
            "message": "Policy enrolled successfully"
        }
    
    @staticmethod
    async def auto_enroll_for_booking(
        session: AsyncSession,
        booking_id: uuid.UUID,
        passenger_details: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Automatically enroll passengers for free accident insurance."""
        try:
            # Get booking details
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            
            if not booking:
                return None
            
            # Get user ID (for guest bookings, we'll use a default user or create one)
            user_id = booking.user_id
            if not user_id:
                # For guest bookings, we need to handle this differently
                # For now, we'll skip insurance for guest bookings
                # In production, you might want to create a temporary user record
                return None
            
            # Prepare booking details for insurance API
            booking_details = {
                "booking_reference": booking.booking_reference,
                "passenger_count": booking.passenger_count,
                "duration_hours": 12,  # This would come from the actual schedule
                "origin": "Lagos",  # This would come from the actual route
                "destination": "Abuja"  # This would come from the actual route
            }
            
            # Call insurance partner API
            insurance_response = await InsuranceService.mock_enroll_policy(
                passenger_details, booking_details
            )
            
            if not insurance_response["success"]:
                return None
            
            # Create insurance policy record
            insurance_policy = InsurancePolicy(
                booking_id=booking_id,
                user_id=user_id,
                policy_number=insurance_response["policy_number"],
                coverage_details_url=insurance_response["coverage_details_url"],
                status=InsuranceStatus.ACTIVE,
                start_date=insurance_response["start_date"],
                end_date=insurance_response["end_date"],
                coverage_amount=insurance_response["coverage_amount"],
                provider_policy_id=insurance_response["provider_policy_id"]
            )
            
            session.add(insurance_policy)
            await session.commit()
            await session.refresh(insurance_policy)
            
            return {
                "id": str(insurance_policy.id),
                "policy_number": insurance_policy.policy_number,
                "coverage_amount": insurance_policy.coverage_amount,
                "start_date": insurance_policy.start_date.isoformat(),
                "end_date": insurance_policy.end_date.isoformat(),
                "status": insurance_policy.status.value
            }
            
        except Exception as e:
            print(f"Error enrolling insurance for booking {booking_id}: {e}")
            return None
    
    @staticmethod
    async def get_policy_by_id(
        session: AsyncSession,
        policy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get insurance policy by ID."""
        result = await session.execute(
            select(InsurancePolicy).where(InsurancePolicy.id == uuid.UUID(policy_id))
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return None
        
        return {
            "id": str(policy.id),
            "booking_id": str(policy.booking_id),
            "user_id": str(policy.user_id),
            "policy_number": policy.policy_number,
            "coverage_details_url": policy.coverage_details_url,
            "status": policy.status.value,
            "start_date": policy.start_date.isoformat(),
            "end_date": policy.end_date.isoformat(),
            "coverage_amount": policy.coverage_amount,
            "provider_policy_id": policy.provider_policy_id,
            "created_at": policy.created_at.isoformat(),
            "updated_at": policy.updated_at.isoformat()
        }
    
    @staticmethod
    async def get_user_policies(
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all insurance policies for a user."""
        query = (
            select(InsurancePolicy)
            .where(InsurancePolicy.user_id == uuid.UUID(user_id))
            .order_by(InsurancePolicy.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(query)
        policies = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "booking_id": str(p.booking_id),
                "user_id": str(p.user_id),
                "policy_number": p.policy_number,
                "coverage_details_url": p.coverage_details_url,
                "status": p.status.value,
                "start_date": p.start_date.isoformat(),
                "end_date": p.end_date.isoformat(),
                "coverage_amount": p.coverage_amount,
                "provider_policy_id": p.provider_policy_id,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in policies
        ]
    
    @staticmethod
    async def get_booking_policy(
        session: AsyncSession,
        booking_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get insurance policy for a specific booking."""
        result = await session.execute(
            select(InsurancePolicy).where(InsurancePolicy.booking_id == uuid.UUID(booking_id))
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return None
        
        return await InsuranceService.get_policy_by_id(session, str(policy.id))
    
    @staticmethod
    async def cancel_policy(
        session: AsyncSession,
        policy_id: str
    ) -> bool:
        """Cancel an insurance policy."""
        result = await session.execute(
            select(InsurancePolicy).where(InsurancePolicy.id == uuid.UUID(policy_id))
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return False
        
        # Check if policy can be cancelled
        if policy.status != InsuranceStatus.ACTIVE:
            return False
        
        # Update policy status
        policy.status = InsuranceStatus.CANCELLED
        policy.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True
    
    @staticmethod
    async def get_active_policies(
        session: AsyncSession,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active insurance policies."""
        query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.status == InsuranceStatus.ACTIVE,
                InsurancePolicy.end_date > datetime.now(timezone.utc)
            )
        )
        
        if user_id:
            query = query.where(InsurancePolicy.user_id == uuid.UUID(user_id))
        
        query = query.order_by(InsurancePolicy.created_at.desc())
        
        result = await session.execute(query)
        policies = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "booking_id": str(p.booking_id),
                "user_id": str(p.user_id),
                "policy_number": p.policy_number,
                "coverage_details_url": p.coverage_details_url,
                "status": p.status.value,
                "start_date": p.start_date.isoformat(),
                "end_date": p.end_date.isoformat(),
                "coverage_amount": p.coverage_amount,
                "provider_policy_id": p.provider_policy_id,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in policies
        ]
    
    @staticmethod
    async def get_insurance_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Get insurance statistics."""
        # Total policies
        total_policies_result = await session.execute(select(InsurancePolicy))
        total_policies = len(total_policies_result.scalars().all())
        
        # Active policies
        active_policies_result = await session.execute(
            select(InsurancePolicy).where(
                and_(
                    InsurancePolicy.status == InsuranceStatus.ACTIVE,
                    InsurancePolicy.end_date > datetime.now(timezone.utc)
                )
            )
        )
        active_policies = len(active_policies_result.scalars().all())
        
        # Total coverage amount
        active_policies_list = active_policies_result.scalars().all()
        total_coverage = sum(policy.coverage_amount for policy in active_policies_list)
        
        # Today's policies
        today = datetime.now().date()
        today_policies_result = await session.execute(
            select(InsurancePolicy).where(
                and_(
                    InsurancePolicy.created_at >= today,
                    InsurancePolicy.created_at < today + timedelta(days=1)
                )
            )
        )
        today_policies = len(today_policies_result.scalars().all())
        
        return {
            "total_policies": total_policies,
            "active_policies": active_policies,
            "total_coverage_amount": float(total_coverage),
            "today_policies": today_policies
        }
    
    @staticmethod
    async def mock_claim_report(
        policy_number: str,
        claim_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock API call to report a claim to insurance partner."""
        # Simulate API delay
        import asyncio
        if _settings.DEBUG:
            await asyncio.sleep(0.05)
        
        # Generate claim reference
        claim_ref = f"CLM{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        return {
            "success": True,
            "claim_reference": claim_ref,
            "policy_number": policy_number,
            "status": "submitted",
            "message": "Claim submitted successfully",
            "estimated_processing_time": "5-7 business days"
        }
    
    @staticmethod
    async def submit_claim(
        session: AsyncSession,
        policy_id: str,
        user_id: str,
        claim_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit an insurance claim."""
        # Mock claim submission
        claim_id = f"CLM{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:6].upper()}"
        
        return {
            "claim_id": claim_id,
            "policy_id": policy_id,
            "status": "submitted",
            "claim_number": f"INS-{claim_id}",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "estimated_processing_time": "5-7 business days"
        }
    
    @staticmethod
    async def get_coverage_details(policy_id: str) -> Dict[str, Any]:
        """Get detailed coverage information for a policy."""
        # Mock coverage details
        return {
            "accident_coverage": {
                "death_benefit": 1000000.0,
                "permanent_disability": 500000.0,
                "temporary_disability": 100000.0,
                "medical_expenses": 200000.0
            },
            "coverage_scope": [
                "Accidental death during travel",
                "Permanent disability from accident",
                "Temporary disability from accident",
                "Medical expenses from accident",
                "Emergency medical evacuation"
            ],
            "exclusions": [
                "Pre-existing medical conditions",
                "Suicide or self-inflicted injuries",
                "War or terrorism",
                "Under influence of drugs/alcohol",
                "Risky activities not related to travel"
            ],
            "claim_process": [
                "Report incident within 48 hours",
                "Submit required documentation",
                "Medical examination if required",
                "Claim review and processing",
                "Payment within 30 days of approval"
            ]
        } 