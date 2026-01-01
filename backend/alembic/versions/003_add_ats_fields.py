"""add ats fields to matches

Revision ID: 003
Revises: 002
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ATS analysis columns to matches table
    op.add_column('matches', sa.Column('ats_score', sa.Float(), nullable=True))
    op.add_column('matches', sa.Column('keyword_matches', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('matches', sa.Column('ats_issues', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove ATS analysis columns
    op.drop_column('matches', 'ats_issues')
    op.drop_column('matches', 'keyword_matches')
    op.drop_column('matches', 'ats_score')
