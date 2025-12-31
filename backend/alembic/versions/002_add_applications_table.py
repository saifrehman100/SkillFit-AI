"""Add applications table

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('match_id', sa.Integer(), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('application_date', sa.DateTime(), nullable=True),
        sa.Column('job_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index('idx_application_user_status', 'applications', ['user_id', 'status'], unique=False)
    op.create_index('idx_application_status', 'applications', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_application_status', table_name='applications')
    op.drop_index('idx_application_user_status', table_name='applications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')

    # Drop table
    op.drop_table('applications')
