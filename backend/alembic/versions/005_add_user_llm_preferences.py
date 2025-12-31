"""Add user LLM preferences

Revision ID: 005
Revises: 004
Create Date: 2025-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add llm_provider and llm_model columns to users table
    op.add_column('users', sa.Column('llm_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('llm_model', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove llm_provider and llm_model columns from users table
    op.drop_column('users', 'llm_model')
    op.drop_column('users', 'llm_provider')
