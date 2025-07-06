import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str 
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application settings
    APP_NAME: str = "Cheetah API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # External API settings
    INSURANCE_API_URL: Optional[str] = None
    INSURANCE_API_KEY: Optional[str] = None
    WIFI_API_URL: Optional[str] = None
    WIFI_API_KEY: Optional[str] = None
    
    # Email/SMS settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    
    # Transport provider settings
    ENABLED_PROVIDERS: str = "abc_transport,guo_transport,pmt"
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True


# Create global settings instance
settings = Settings()
