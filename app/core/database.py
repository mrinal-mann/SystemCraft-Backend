"""
Database Configuration for SQLAlchemy

Re-exports the database utilities from app.db for backward compatibility.
This module maintains the same interface as the previous Prisma configuration.

Design Decisions:
- Using async SQLAlchemy for better performance
- Single engine instance (created on import, disposed on shutdown)
- get_db dependency returns AsyncSession for route handlers
"""

# Re-export from the new db module for backward compatibility
from app.db.session import (
    async_engine,
    AsyncSessionLocal,
    get_db,
    init_db,
    close_db,
)

# Alias for lifespan functions (matching previous interface)
connect_db = init_db
disconnect_db = close_db

__all__ = [
    "async_engine",
    "AsyncSessionLocal", 
    "get_db",
    "connect_db",
    "disconnect_db",
    "init_db",
    "close_db",
]
