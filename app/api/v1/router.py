"""
API v1 Router

Central router that aggregates all v1 endpoints.

Design Decision:
- Versioned API allows future breaking changes without disrupting clients
- Each domain (auth, projects) gets its own router for separation
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, projects, analysis

api_router = APIRouter()

# Authentication routes - no prefix, already contextually clear
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Project management routes
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["Projects"]
)

# Analysis routes - could be nested under projects, but keeping separate
# for clarity and potential future expansion
api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"]
)
