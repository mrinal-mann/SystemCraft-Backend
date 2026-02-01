"""fix_enum_types

Revision ID: 6acd337aa6a4
Revises: d629d68c4125
Create Date: 2026-02-01 20:09:00.668365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6acd337aa6a4'
down_revision: Union[str, Sequence[str], None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ENUM types if they don't exist."""
    
    # Create ENUMs using raw SQL with exception handling for IF NOT EXISTS
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE project_status AS ENUM ('DRAFT', 'IN_PROGRESS', 'ANALYZED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE suggestion_category AS ENUM (
                'CACHING', 'SCALABILITY', 'SECURITY', 'RELIABILITY',
                'PERFORMANCE', 'DATABASE', 'API_DESIGN', 'GENERAL'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE suggestion_severity AS ENUM ('INFO', 'WARNING', 'CRITICAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE suggestion_status AS ENUM ('OPEN', 'ADDRESSED', 'IGNORED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    """Drop ENUM types if they exist."""
    op.execute("DROP TYPE IF EXISTS suggestion_status")
    op.execute("DROP TYPE IF EXISTS suggestion_severity")
    op.execute("DROP TYPE IF EXISTS suggestion_category")
    op.execute("DROP TYPE IF EXISTS project_status")
