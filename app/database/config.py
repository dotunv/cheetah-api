import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str 
    SQL_ECHO: bool = False
    
    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application settings
    APP_NAME: str = "Cheetah API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS settings
    # Comma-separated list of origins, e.g. "http://localhost:3000,http://127.0.0.1:5173"
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
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

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        """Normalize certain fields loaded from env.

        This is defensive to handle cases where values in --env-file are wrapped
        in quotes (which Docker does not strip). Those quotes break URL parsing.
        """
        def _strip_quotes(value: Optional[str]) -> Optional[str]:
            if value is None:
                return value
            v = value.strip()
            if (v.startswith("\"") and v.endswith("\"")) or (v.startswith("'") and v.endswith("'")):
                return v[1:-1]
            return v

        # Normalize strings that are sensitive to surrounding quotes
        self.DATABASE_URL = _strip_quotes(self.DATABASE_URL) or self.DATABASE_URL
        self.SECRET_KEY = _strip_quotes(self.SECRET_KEY) or self.SECRET_KEY
        self.INSURANCE_API_URL = _strip_quotes(self.INSURANCE_API_URL)
        self.WIFI_API_URL = _strip_quotes(self.WIFI_API_URL)


# Create settings instance (cached)
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
