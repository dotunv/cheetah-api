import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.middleware.gzip import GZipMiddleware

from .database.database import lifespan
from .database.config import get_settings

# Import routers
from .routers import users, auth, bookings, payments, insurance, wifi, providers, analytics


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application lifespan manager."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    # Reduce noisy SQL logs unless explicitly enabled
    settings = get_settings()
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.INFO if settings.SQL_ECHO else logging.WARNING)
    logger.info("Starting Cheetah API application")
    async with lifespan(app):
        yield
    logger.info("Shutting down Cheetah API application")


app = FastAPI(
    title=get_settings().APP_NAME,
    description="InterCity Transportation Aggregator Platform API",
    version=get_settings().APP_VERSION,
    lifespan=app_lifespan,
    docs_url="/docs" if get_settings().DEBUG else None,
    redoc_url="/redoc" if get_settings().DEBUG else None,
)

# Add CORS middleware (configurable)
_settings = get_settings()
_origins = [o.strip() for o in _settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()] or ["*"]
_allow_credentials = _settings.CORS_ALLOW_CREDENTIALS
# If wildcard origins are used, credentials cannot be allowed per CORS spec
if _origins == ["*"] and _allow_credentials:
    logging.getLogger(__name__).warning(
        "CORS misconfiguration: allow_credentials=True with '*' origins is invalid. "
        "Forcing allow_credentials=False. Set explicit origins in CORS_ALLOW_ORIGINS to enable credentials."
    )
    _allow_credentials = False
_methods = [m.strip() for m in _settings.CORS_ALLOW_METHODS.split(",")] if _settings.CORS_ALLOW_METHODS != "*" else ["*"]
_headers = [h.strip() for h in _settings.CORS_ALLOW_HEADERS.split(",")] if _settings.CORS_ALLOW_HEADERS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,  # ✅ FIXED: Using dynamic origins from settings
    allow_credentials=_allow_credentials,  # ✅ FIXED: Using dynamic credentials setting
    allow_methods=_methods,  # ✅ FIXED: Using dynamic methods setting
    allow_headers=_headers,  # ✅ FIXED: Using dynamic headers setting
)

# Enable gzip compression for large responses
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "Welcome to Cheetah API!",
            "description": "InterCity Transportation Aggregator Platform",
            "status": "running",
            "version": get_settings().APP_VERSION,
            "docs": "/docs" if get_settings().DEBUG else "Documentation disabled in production"
        }
    )


@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "cheetah-api",
            "version": get_settings().APP_VERSION
        }
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(insurance.router, prefix="/insurance-policies", tags=["Insurance"])
app.include_router(wifi.router, prefix="/wifi-codes", tags=["WiFi"])
app.include_router(providers.router, prefix="/providers", tags=["Transport Providers"])
app.include_router(analytics.router, prefix="/admin/analytics", tags=["Analytics"])

