"""fix_status_column_type

Revision ID: 697fc00418c8
Revises: 6acd337aa6a4
Create Date: 2026-02-01 20:13:12.730255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '697fc00418c8'
down_revision: Union[str, Sequence[str], None] = '6acd337aa6a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix the status column to use lowercase project_status enum type."""
    
    # Step 1: Drop the default value first (it references the old type)
    op.execute("ALTER TABLE projects ALTER COLUMN status DROP DEFAULT")
    
    # Step 2: Alter the status column to use the lowercase project_status type
    # This handles the case where the column was created with "ProjectStatus" (quoted)
    # but SQLAlchemy expects project_status (unquoted/lowercase)
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN status TYPE project_status 
        USING status::text::project_status
    """)
    
    # Step 3: Set the default value back using the new type
    op.execute("ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'DRAFT'")
    
    # Drop the old "ProjectStatus" type if it exists
    op.execute('DROP TYPE IF EXISTS "ProjectStatus"')


def downgrade() -> None:
    """Downgrade not supported for this migration."""
    pass

