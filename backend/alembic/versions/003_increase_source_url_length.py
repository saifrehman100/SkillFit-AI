"""increase source_url length

Revision ID: 003
Revises: 002
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema: Change source_url from VARCHAR(512) to TEXT."""
    # Alter source_url column to TEXT for unlimited length
    # This allows LinkedIn URLs with long tracking parameters
    op.alter_column('jobs', 'source_url',
                    type_=sa.Text(),
                    existing_type=sa.String(512),
                    existing_nullable=True)


def downgrade():
    """Downgrade schema: Revert source_url to VARCHAR(512)."""
    op.alter_column('jobs', 'source_url',
                    type_=sa.String(512),
                    existing_type=sa.Text(),
                    existing_nullable=True)
