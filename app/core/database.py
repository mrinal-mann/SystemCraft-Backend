"""
Database Configuration for Prisma

Provides the Prisma client instance and dependency for FastAPI.

Design Decisions:
- Using async Prisma client for better performance
- Single client instance (connect on startup, disconnect on shutdown)
- get_db dependency for route handlers

Note: After running `prisma generate`, the client becomes available.
"""

from prisma import Prisma

# Global Prisma client instance
prisma = Prisma()


async def connect_db():
    """Connect to database on application startup."""
    await prisma.connect()


async def disconnect_db():
    """Disconnect from database on application shutdown."""
    await prisma.disconnect()


async def get_db() -> Prisma:
    """
    Database dependency for route handlers.
    
    Returns the connected Prisma client instance.
    
    Usage:
        @router.get("/items")
        async def get_items(db: Prisma = Depends(get_db)):
            items = await db.item.find_many()
            ...
    """
    return prisma
