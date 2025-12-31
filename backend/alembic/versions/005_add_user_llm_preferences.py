"""Add user LLM preferences and subscription tracking

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
    # Add LLM preferences (system manages API keys)
    op.add_column('users', sa.Column('llm_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('llm_model', sa.String(length=100), nullable=True))

    # Add subscription and usage tracking
    op.add_column('users', sa.Column('plan', sa.String(length=20), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('matches_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove subscription fields
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'matches_used')
    op.drop_column('users', 'plan')

    # Remove LLM preference fields
    op.drop_column('users', 'llm_model')
    op.drop_column('users', 'llm_provider')
