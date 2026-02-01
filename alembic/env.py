"""
Alembic Async Environment Configuration

This env.py is configured for:
- Async SQLAlchemy with asyncpg driver
- Reading DATABASE_URL from environment variables
- Autogenerate support for all models
- Proper handling of both offline and online migrations
- SSL support for cloud databases (Neon, Supabase, etc.)

Production-grade features:
- Environment variable based configuration
- Automatic URL conversion for async driver
- All models imported for autogenerate
"""

import asyncio
import os
import ssl
import sys
from logging.config import fileConfig
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import settings and models
from app.core.config import settings
from app.db.base import Base

# Import all models here to register them with Base.metadata
# This is REQUIRED for autogenerate to detect model changes
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.design import DesignDetails, DesignVersion  # noqa: F401
from app.models.suggestion import Suggestion  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


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


# Get async URL and connect args
ASYNC_DATABASE_URL, CONNECT_ARGS = get_async_database_url(settings.DATABASE_URL)

# Override sqlalchemy.url with the async version from environment
config.set_main_option("sqlalchemy.url", ASYNC_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
# This is the MetaData object that contains all models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    
    Useful for generating SQL scripts without database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare types during autogenerate
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with the given connection.
    
    This is a helper function used by run_async_migrations.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Compare types during autogenerate
        compare_type=True,
        # Compare server defaults  
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an async Engine
    and associate a connection with the context.
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # Create engine with SSL connect args
    connectable = create_async_engine(
        ASYNC_DATABASE_URL,
        poolclass=pool.NullPool,
        connect_args=CONNECT_ARGS,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Wraps the async migration function for the sync Alembic CLI.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
