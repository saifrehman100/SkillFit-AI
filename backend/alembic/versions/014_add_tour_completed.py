"""add tour_completed

Revision ID: 014
Revises: 013
Create Date: 2026-01-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    # Add tour_completed column to users table
    op.add_column('users', sa.Column('tour_completed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Remove tour_completed column from users table
    op.drop_column('users', 'tour_completed')
