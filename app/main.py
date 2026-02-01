"""
Main FastAPI Application Entry Point

This is the central orchestrator that:
1. Creates the FastAPI app instance
2. Configures CORS for frontend communication
3. Registers all API routers
4. Sets up database connection lifecycle
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import connect_db, disconnect_db

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set specific loggers to INFO level
logging.getLogger("app.services.analysis_service").setLevel(logging.INFO)
logging.getLogger("app.llm.openrouter_client").setLevel(logging.INFO)
logging.getLogger("app.api.v1.endpoints.analysis").setLevel(logging.INFO)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Connects to database on startup
    - Disconnects from database on shutdown
    """
    # Startup
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered System Design Mentor for students and early-career engineers",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
# For MVP, allowing localhost origins. In production, restrict to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api/v1 prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and container orchestration.
    Returns simple OK status - no auth required.
    """
    return {"status": "healthy", "version": "1.0.0"}
