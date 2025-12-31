"""increase application job_url length

Revision ID: 004
Revises: 003
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema: Change job_url from VARCHAR(500) to TEXT."""
    # Alter job_url column to TEXT for unlimited length
    # This allows LinkedIn URLs with long tracking parameters
    op.alter_column('applications', 'job_url',
                    type_=sa.Text(),
                    existing_type=sa.String(500),
                    existing_nullable=True)


def downgrade():
    """Downgrade schema: Revert job_url to VARCHAR(500)."""
    op.alter_column('applications', 'job_url',
                    type_=sa.String(500),
                    existing_type=sa.Text(),
                    existing_nullable=True)
