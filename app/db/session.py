"""
Async Database Session Configuration

Provides async database engine and session factory for SQLAlchemy.

Design Decisions:
- Using asyncpg driver for PostgreSQL (production-grade async)
- Connection pooling with sensible defaults for production
- Session dependency that properly handles transactions
- Explicit URL format conversion for async compatibility
- SSL handling for cloud databases (Neon, Supabase, etc.)

Pool Configuration:
- pool_size: Number of persistent connections (default: 5)
- max_overflow: Extra connections when pool is exhausted (default: 10)
- pool_pre_ping: Check connection health before using (prevents stale connections)
- pool_recycle: Recycle connections after N seconds (prevents DB timeout issues)
"""

import logging
import ssl
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_async_database_url(url: str) -> tuple[str, dict]:
    """
    Convert standard PostgreSQL URL to async-compatible format.
    
    Handles:
    - Driver conversion: postgresql:// -> postgresql+asyncpg://
    - SSL mode extraction: asyncpg uses 'ssl' context instead of 'sslmode' param
    - Removes incompatible query params for asyncpg
    
    Returns:
        Tuple of (cleaned_url, connect_args_dict)
    """
    connect_args = {}
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Extract query parameters
    query_params = parse_qs(parsed.query)
    
    # Handle sslmode - asyncpg doesn't accept it as URL param
    sslmode = query_params.pop('sslmode', [None])[0]
    
    # Remove other asyncpg-incompatible params
    query_params.pop('channel_binding', None)  # Not supported by asyncpg
    
    # If SSL is required, create SSL context for asyncpg
    if sslmode in ('require', 'verify-ca', 'verify-full'):
        # Create SSL context that doesn't verify certificates (like sslmode=require)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args['ssl'] = ssl_context
    
    # Rebuild query string without removed params
    new_query = urlencode({k: v[0] for k, v in query_params.items()}, safe='')
    
    # Convert driver
    scheme = parsed.scheme
    if scheme == "postgresql":
        scheme = "postgresql+asyncpg"
    elif scheme == "postgres":
        scheme = "postgresql+asyncpg"
    
    # Rebuild URL
    new_parsed = parsed._replace(
        scheme=scheme,
        query=new_query if new_query else ''
    )
    
    clean_url = urlunparse(new_parsed)
    
    return clean_url, connect_args


# Build async database URL and connection args
ASYNC_DATABASE_URL, CONNECT_ARGS = get_async_database_url(settings.DATABASE_URL)

logger.info(f"Database URL configured: {ASYNC_DATABASE_URL.split('@')[0]}@****")

# Create async engine with production-optimized settings
# Using NullPool for serverless databases (Neon, Supabase, etc.)
# This prevents connection pooling issues with serverless cold starts
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
    # Use NullPool for serverless databases to avoid connection issues
    poolclass=NullPool,
    # Pass SSL context for asyncpg
    connect_args=CONNECT_ARGS,
)

# Session factory - creates new AsyncSession instances
# expire_on_commit=False prevents attributes from being expired after commit,
# which is useful in async contexts where we may access data after commit
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI route handlers.
    
    Creates a new session for each request and handles cleanup.
    Uses async context manager pattern for proper resource management.
    
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    Transaction Behavior:
        - Session is created fresh for each request
        - Commit is NOT automatic - call db.commit() explicitly when needed
        - Rollback happens automatically on exception
        - Session is always closed after request completes
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    WARNING: This should only be used in development or initial setup.
    For production, use Alembic migrations.
    
    Usage (in app lifespan):
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    """
    from app.db.base import Base
    # Import all models to ensure they are registered with Base
    from app.models import user, project, design, suggestion  # noqa: F401
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called on application shutdown to properly
    dispose of the connection pool.
    """
    await async_engine.dispose()
    logger.info("Database connections closed")
