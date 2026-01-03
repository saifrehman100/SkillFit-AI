"""add soft delete

Revision ID: 013
Revises: 012
Create Date: 2026-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    # Add deleted_at column to resumes table
    op.add_column('resumes', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Add deleted_at column to jobs table
    op.add_column('jobs', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove deleted_at column from jobs table
    op.drop_column('jobs', 'deleted_at')

    # Remove deleted_at column from resumes table
    op.drop_column('resumes', 'deleted_at')
