"""add usage tracking fields

Revision ID: 012
Revises: 011
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    # Add usage tracking fields to users table
    op.add_column('users', sa.Column('resume_rewrites_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('cover_letters_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('interview_preps_used', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # Remove usage tracking fields from users table
    op.drop_column('users', 'interview_preps_used')
    op.drop_column('users', 'cover_letters_used')
    op.drop_column('users', 'resume_rewrites_used')
