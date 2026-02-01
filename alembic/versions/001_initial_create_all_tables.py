"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-01

This migration creates all initial database tables:
- users: User accounts for authentication
- projects: System design projects
- design_details: Current design content (1:1 with projects)
- design_versions: Version history for designs
- suggestions: AI-generated improvement suggestions

Enums created:
- project_status: DRAFT, IN_PROGRESS, ANALYZED
- suggestion_category: CACHING, SCALABILITY, SECURITY, etc.
- suggestion_severity: INFO, WARNING, CRITICAL
- suggestion_status: OPEN, ADDRESSED, IGNORED
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables and enums."""
    
    # Create ENUM types first
    project_status_enum = postgresql.ENUM(
        'DRAFT', 'IN_PROGRESS', 'ANALYZED',
        name='project_status',
        create_type=True
    )
    project_status_enum.create(op.get_bind(), checkfirst=True)
    
    suggestion_category_enum = postgresql.ENUM(
        'CACHING', 'SCALABILITY', 'SECURITY', 'RELIABILITY',
        'PERFORMANCE', 'DATABASE', 'API_DESIGN', 'GENERAL',
        name='suggestion_category',
        create_type=True
    )
    suggestion_category_enum.create(op.get_bind(), checkfirst=True)
    
    suggestion_severity_enum = postgresql.ENUM(
        'INFO', 'WARNING', 'CRITICAL',
        name='suggestion_severity',
        create_type=True
    )
    suggestion_severity_enum.create(op.get_bind(), checkfirst=True)
    
    suggestion_status_enum = postgresql.ENUM(
        'OPEN', 'ADDRESSED', 'IGNORED',
        name='suggestion_status',
        create_type=True
    )
    suggestion_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'IN_PROGRESS', 'ANALYZED', name='project_status'), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('maturity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('maturity_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_projects_owner_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects'))
    )
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    
    # Create design_details table (one-to-one with projects)
    op.create_table(
        'design_details',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_design_details_project_id_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_design_details')),
        sa.UniqueConstraint('project_id', name=op.f('uq_design_details_project_id'))
    )
    op.create_index(op.f('ix_design_details_project_id'), 'design_details', ['project_id'], unique=True)
    
    # Create design_versions table
    op.create_table(
        'design_versions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('maturity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('suggestions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_design_versions_project_id_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_design_versions')),
        sa.UniqueConstraint('project_id', 'version_number', name='uq_design_versions_project_version')
    )
    op.create_index(op.f('ix_design_versions_project_id'), 'design_versions', ['project_id'], unique=False)
    
    # Create suggestions table
    op.create_table(
        'suggestions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum(
            'CACHING', 'SCALABILITY', 'SECURITY', 'RELIABILITY',
            'PERFORMANCE', 'DATABASE', 'API_DESIGN', 'GENERAL',
            name='suggestion_category'
        ), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'CRITICAL', name='suggestion_severity'), nullable=False),
        sa.Column('design_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'ADDRESSED', 'IGNORED', name='suggestion_status'), nullable=False),
        sa.Column('addressed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('addressed_in_version', sa.Integer(), nullable=True),
        sa.Column('trigger_keywords', postgresql.ARRAY(sa.String(length=100)), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_suggestions_project_id_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_suggestions'))
    )
    op.create_index(op.f('ix_suggestions_project_id'), 'suggestions', ['project_id'], unique=False)


def downgrade() -> None:
    """Drop all tables and enums."""
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index(op.f('ix_suggestions_project_id'), table_name='suggestions')
    op.drop_table('suggestions')
    
    op.drop_index(op.f('ix_design_versions_project_id'), table_name='design_versions')
    op.drop_table('design_versions')
    
    op.drop_index(op.f('ix_design_details_project_id'), table_name='design_details')
    op.drop_table('design_details')
    
    op.drop_index(op.f('ix_projects_owner_id'), table_name='projects')
    op.drop_table('projects')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS suggestion_status")
    op.execute("DROP TYPE IF EXISTS suggestion_severity")
    op.execute("DROP TYPE IF EXISTS suggestion_category")
    op.execute("DROP TYPE IF EXISTS project_status")
