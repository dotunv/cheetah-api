from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database.database import lifespan
from database.config import settings

# Import routers
from routers import users, auth, bookings


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application lifespan manager."""
    async with lifespan(app):
        yield


app = FastAPI(
    title=settings.APP_NAME,
    description="InterCity Transportation Aggregator Platform API",
    version=settings.APP_VERSION,
    lifespan=app_lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
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
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
        }
    )


@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "cheetah-api",
            "version": settings.APP_VERSION
        }
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=settings.DEBUG
    )
