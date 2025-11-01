from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..database.config import get_settings
from ..database.models import User, UserRole


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT handling."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, get_settings().SECRET_KEY, algorithm=get_settings().ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        # Get user by email
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: Union[str, uuid.UUID]) -> Optional[User]:
        """Get user by ID."""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        role: UserRole = UserRole.CUSTOMER
    ) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = await AuthService.get_user_by_email(session, email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role,
            is_active=True,
            is_verified=False  # Will be verified via email/SMS in production
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user_password(session: AsyncSession, user_id: uuid.UUID, new_password: str) -> bool:
        """Update user password."""
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            return False
        
        user.hashed_password = AuthService.get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True
    
    @staticmethod
    async def deactivate_user(session: AsyncSession, user_id: uuid.UUID) -> bool:
        """Deactivate a user account."""
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True
    
    @staticmethod
    async def activate_user(session: AsyncSession, user_id: uuid.UUID) -> bool:
        """Activate a user account."""
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            return False
        
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True
    
    @staticmethod
    def generate_verification_token(user_id: uuid.UUID) -> str:
        """Generate email verification token."""
        data = {
            "sub": str(user_id),
            "type": "email_verification",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        return AuthService.create_access_token(data)
    
    @staticmethod
    def generate_password_reset_token(email: str) -> str:
        """Generate password reset token."""
        data = {
            "sub": email,
            "type": "password_reset",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        return AuthService.create_access_token(data)
