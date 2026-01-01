"""add generated content fields

Revision ID: 011
Revises: 010
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Add generated content fields to matches table
    op.add_column('matches', sa.Column('interview_prep_data', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('matches', sa.Column('cover_letter_data', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('matches', sa.Column('improved_resume_data', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    # Remove generated content fields from matches table
    op.drop_column('matches', 'improved_resume_data')
    op.drop_column('matches', 'cover_letter_data')
    op.drop_column('matches', 'interview_prep_data')
