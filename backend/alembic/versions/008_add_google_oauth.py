"""add google oauth

Revision ID: 008
Revises: 007
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable for OAuth users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=True)

    # Add google_id column
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))

    # Create unique index on google_id
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)


def downgrade() -> None:
    # Remove index and column
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'google_id')

    # Make hashed_password non-nullable again
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=False)
