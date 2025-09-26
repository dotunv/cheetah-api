import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .database.database import lifespan
from .database.config import get_settings

# Import routers
from .routers import users, auth, bookings, payments


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application lifespan manager."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

