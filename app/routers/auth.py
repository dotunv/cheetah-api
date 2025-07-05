from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_db
from ..database.config import settings
from ..services.auth_service import AuthService
from ..services.user_service import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    user_email: str
    user_role: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db)
) -> Optional[dict]:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthService.verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = await AuthService.get_user_by_id(session, user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    try:
        user = await AuthService.create_user(
            session=session,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone
        )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    """Login and get access token."""
    user = await AuthService.authenticate_user(
        session=session,
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        user_email=user.email,
        user_role=user.role.value
    )


@router.post("/login", response_model=Token)
async def login_with_json(
    login_data: UserLogin,
    session: AsyncSession = Depends(get_db)
):
    """Login with JSON data and get access token."""
    user = await AuthService.authenticate_user(
        session=session,
        email=login_data.email,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        user_email=user.email,
        user_role=user.role.value
    )


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    user_id = current_user["id"]
    profile = await UserService.get_user_profile(session, user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile


@router.post("/password-reset-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    session: AsyncSession = Depends(get_db)
):
    """Request password reset token."""
    user = await AuthService.get_user_by_email(session, reset_request.email)
    
    if not user:
        # Don't reveal if user exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate password reset token
    reset_token = AuthService.generate_password_reset_token(reset_request.email)
    
    # In production, send email with reset link
    # For now, just return the token (remove this in production)
    return {
        "message": "Password reset token generated",
        "token": reset_token  # Remove this in production
    }


@router.post("/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    session: AsyncSession = Depends(get_db)
):
    """Reset password using token."""
    payload = AuthService.verify_token(reset_data.token)
    
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    email = payload.get("sub")
    user = await AuthService.get_user_by_email(session, email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    success = await AuthService.update_user_password(
        session=session,
        user_id=user.id,
        new_password=reset_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout():
    """Logout endpoint (client should discard token)."""
    return {"message": "Successfully logged out"}


@router.get("/verify-token")
async def verify_token(
    current_user: dict = Depends(get_current_user)
):
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user": current_user
    }
