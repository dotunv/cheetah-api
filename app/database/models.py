from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from .database import Base


class UserRole(str, enum.Enum):
    """User roles in the system."""
    CUSTOMER = "customer"
    ADMIN = "admin"
    PROVIDER = "provider"


class TransportType(str, enum.Enum):
    """Types of transportation."""
    BUS = "bus"
    TRAIN = "train"
    FERRY = "ferry"


class BookingStatus(str, enum.Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class InsuranceStatus(str, enum.Enum):
    """Insurance policy status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class WifiUsageStatus(str, enum.Enum):
    """WiFi code usage status."""
    UNUSED = "unused"
    ACTIVE = "active"
    EXPIRED = "expired"
    USED = "used"


class User(Base):
    """User model for customer accounts."""
    __tablename__ = "users"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = Column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = Column(String(20), unique=True, index=True)
    first_name: Mapped[str] = Column(String(100), nullable=False)
    last_name: Mapped[str] = Column(String(100), nullable=False)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    role: Mapped[UserRole] = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_verified: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="user")
    insurance_policies: Mapped[List["InsurancePolicy"]] = relationship("InsurancePolicy", back_populates="user")


class TransportProvider(Base):
    """Transport provider model (ABC Transport, G.U.O Transport, PMT, etc.)."""
    __tablename__ = "transport_providers"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String(255), nullable=False, unique=True)
    code: Mapped[str] = Column(String(50), unique=True, nullable=False)  # e.g., "abc", "guo", "pmt"
    transport_type: Mapped[TransportType] = Column(Enum(TransportType), default=TransportType.BUS)
    contact_email: Mapped[Optional[str]] = Column(String(255))
    contact_phone: Mapped[Optional[str]] = Column(String(20))
    website_url: Mapped[Optional[str]] = Column(String(500))
    api_endpoint: Mapped[Optional[str]] = Column(String(500))
    api_key: Mapped[Optional[str]] = Column(String(255))
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    routes: Mapped[List["Route"]] = relationship("Route", back_populates="provider")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="provider")


class Route(Base):
    """Route model for transportation routes."""
    __tablename__ = "routes"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("transport_providers.id"), nullable=False)
    origin: Mapped[str] = Column(String(255), nullable=False)
    destination: Mapped[str] = Column(String(255), nullable=False)
    route_code: Mapped[str] = Column(String(100), nullable=False)  # Provider's internal route code
    distance_km: Mapped[Optional[float]] = Column(Float)
    estimated_duration_hours: Mapped[Optional[float]] = Column(Float)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    provider: Mapped["TransportProvider"] = relationship("TransportProvider", back_populates="routes")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="route")


class Schedule(Base):
    """Schedule model for transportation schedules."""
    __tablename__ = "schedules"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("transport_providers.id"), nullable=False)
    route_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    schedule_code: Mapped[str] = Column(String(100), nullable=False)  # Provider's internal schedule code
    departure_time: Mapped[datetime] = Column(DateTime, nullable=False)
    arrival_time: Mapped[datetime] = Column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = Column(Integer, nullable=False)
    total_seats: Mapped[int] = Column(Integer, nullable=False)
    available_seats: Mapped[int] = Column(Integer, nullable=False)
    base_price: Mapped[float] = Column(Float, nullable=False)
    vehicle_type: Mapped[Optional[str]] = Column(String(100))  # e.g., "Sprinter", "Luxury Bus"
    amenities: Mapped[Optional[str]] = Column(Text)  # JSON string of amenities
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    provider: Mapped["TransportProvider"] = relationship("TransportProvider", back_populates="schedules")
    route: Mapped["Route"] = relationship("Route", back_populates="schedules")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="schedule")


class Booking(Base):
    """Booking model for customer reservations."""
    __tablename__ = "bookings"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_reference: Mapped[str] = Column(String(50), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[UUID]] = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Optional for guest bookings
    guest_email: Mapped[Optional[str]] = Column(String(255))  # For guest bookings
    guest_phone: Mapped[Optional[str]] = Column(String(20))  # For guest bookings
    schedule_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=False)
    passenger_count: Mapped[int] = Column(Integer, nullable=False, default=1)
    total_amount: Mapped[float] = Column(Float, nullable=False)
    booking_status: Mapped[BookingStatus] = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    payment_status: Mapped[PaymentStatus] = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    passenger_details: Mapped[str] = Column(Text, nullable=False)  # JSON string of passenger details
    provider_booking_reference: Mapped[Optional[str]] = Column(String(100))  # Provider's booking reference
    notes: Mapped[Optional[str]] = Column(Text)
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="bookings")
    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="bookings")
    insurance_policy: Mapped[Optional["InsurancePolicy"]] = relationship("InsurancePolicy", back_populates="booking", uselist=False)
    wifi_code: Mapped[Optional["WifiCode"]] = relationship("WifiCode", back_populates="booking", uselist=False)


class InsurancePolicy(Base):
    """Insurance policy model for free accident insurance."""
    __tablename__ = "insurance_policies"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    user_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_number: Mapped[str] = Column(String(100), unique=True, nullable=False)
    coverage_details_url: Mapped[Optional[str]] = Column(String(500))
    status: Mapped[InsuranceStatus] = Column(Enum(InsuranceStatus), default=InsuranceStatus.ACTIVE)
    start_date: Mapped[datetime] = Column(DateTime, nullable=False)
    end_date: Mapped[datetime] = Column(DateTime, nullable=False)
    coverage_amount: Mapped[float] = Column(Float, nullable=False, default=1000000.0)  # 1M Naira default
    provider_policy_id: Mapped[Optional[str]] = Column(String(100))  # Insurance partner's policy ID
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="insurance_policy")
    user: Mapped["User"] = relationship("User", back_populates="insurance_policies")


class WifiCode(Base):
    """WiFi code model for free WiFi access."""
    __tablename__ = "wifi_codes"
    
    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    code: Mapped[str] = Column(String(50), unique=True, nullable=False)
    qr_code_data: Mapped[Optional[str]] = Column(Text)  # QR code data or URL
    expiry_time: Mapped[datetime] = Column(DateTime, nullable=False)
    usage_status: Mapped[WifiUsageStatus] = Column(Enum(WifiUsageStatus), default=WifiUsageStatus.UNUSED)
    bandwidth_limit_mb: Mapped[Optional[int]] = Column(Integer, default=500)  # 500MB default
    provider_code_id: Mapped[Optional[str]] = Column(String(100))  # WiFi provider's code ID
    created_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="wifi_code")
