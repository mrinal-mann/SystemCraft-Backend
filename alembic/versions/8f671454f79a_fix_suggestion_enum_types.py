"""fix_suggestion_enum_types

Revision ID: 8f671454f79a
Revises: 697fc00418c8
Create Date: 2026-02-01 20:20:16.760744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f671454f79a'
down_revision: Union[str, Sequence[str], None] = '697fc00418c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix the suggestions table ENUM columns to use lowercase types."""
    
    # Fix status column (SuggestionStatus -> suggestion_status)
    op.execute("ALTER TABLE suggestions ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE suggestions 
        ALTER COLUMN status TYPE suggestion_status 
        USING status::text::suggestion_status
    """)
    op.execute("ALTER TABLE suggestions ALTER COLUMN status SET DEFAULT 'OPEN'")
    
    # Fix category column (SuggestionCategory -> suggestion_category)
    op.execute("ALTER TABLE suggestions ALTER COLUMN category DROP DEFAULT")
    op.execute("""
        ALTER TABLE suggestions 
        ALTER COLUMN category TYPE suggestion_category 
        USING category::text::suggestion_category
    """)
    op.execute("ALTER TABLE suggestions ALTER COLUMN category SET DEFAULT 'GENERAL'")
    
    # Fix severity column (SuggestionSeverity -> suggestion_severity)
    op.execute("ALTER TABLE suggestions ALTER COLUMN severity DROP DEFAULT")
    op.execute("""
        ALTER TABLE suggestions 
        ALTER COLUMN severity TYPE suggestion_severity 
        USING severity::text::suggestion_severity
    """)
    op.execute("ALTER TABLE suggestions ALTER COLUMN severity SET DEFAULT 'INFO'")
    
    # Drop the old case-sensitive types if they exist
    op.execute('DROP TYPE IF EXISTS "SuggestionStatus"')
    op.execute('DROP TYPE IF EXISTS "SuggestionCategory"')
    op.execute('DROP TYPE IF EXISTS "SuggestionSeverity"')


def downgrade() -> None:
    """Downgrade not supported for this migration."""
    pass

