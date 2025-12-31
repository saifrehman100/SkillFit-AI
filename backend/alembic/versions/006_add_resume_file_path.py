"""Add file_path to resumes table

Revision ID: 006
Revises: 005
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add file_path column for GCS storage
    op.add_column('resumes', sa.Column('file_path', sa.String(length=512), nullable=True))


def downgrade() -> None:
    # Remove file_path column
    op.drop_column('resumes', 'file_path')
