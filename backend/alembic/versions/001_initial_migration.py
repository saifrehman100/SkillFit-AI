"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('api_key', sa.String(length=64), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('llm_api_keys', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_api_key'), 'users', ['api_key'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('upload_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    op.create_index(op.f('ix_resumes_upload_hash'), 'resumes', ['upload_hash'], unique=False)

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('source_url', sa.String(length=512), nullable=True),
        sa.Column('job_hash', sa.String(length=64), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_job_hash'), 'jobs', ['job_hash'], unique=False)

    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
        sa.Column('missing_skills', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('llm_provider', sa.String(length=50), nullable=True),
        sa.Column('llm_model', sa.String(length=100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_matches_id'), 'matches', ['id'], unique=False)
    op.create_index('idx_match_score', 'matches', ['match_score'], unique=False)
    op.create_index('idx_match_user_resume_job', 'matches', ['user_id', 'resume_id', 'job_id'], unique=False)

    # Create batch_jobs table
    op.create_table(
        'batch_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('processed_items', sa.Integer(), nullable=True),
        sa.Column('failed_items', sa.Integer(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_batch_jobs_celery_task_id'), 'batch_jobs', ['celery_task_id'], unique=False)
    op.create_index(op.f('ix_batch_jobs_id'), 'batch_jobs', ['id'], unique=False)
    op.create_index('idx_batch_status', 'batch_jobs', ['status'], unique=False)
    op.create_index('idx_batch_user_status', 'batch_jobs', ['user_id', 'status'], unique=False)

    # Create api_usage table
    op.create_table(
        'api_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('llm_provider', sa.String(length=50), nullable=True),
        sa.Column('llm_model', sa.String(length=100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_usage_id'), 'api_usage', ['id'], unique=False)
    op.create_index('idx_usage_endpoint', 'api_usage', ['endpoint'], unique=False)
    op.create_index('idx_usage_user_created', 'api_usage', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_usage_user_created', table_name='api_usage')
    op.drop_index('idx_usage_endpoint', table_name='api_usage')
    op.drop_index(op.f('ix_api_usage_id'), table_name='api_usage')
    op.drop_table('api_usage')

    op.drop_index('idx_batch_user_status', table_name='batch_jobs')
    op.drop_index('idx_batch_status', table_name='batch_jobs')
    op.drop_index(op.f('ix_batch_jobs_id'), table_name='batch_jobs')
    op.drop_index(op.f('ix_batch_jobs_celery_task_id'), table_name='batch_jobs')
    op.drop_table('batch_jobs')

    op.drop_index('idx_match_user_resume_job', table_name='matches')
    op.drop_index('idx_match_score', table_name='matches')
    op.drop_index(op.f('ix_matches_id'), table_name='matches')
    op.drop_table('matches')

    op.drop_index(op.f('ix_jobs_job_hash'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')

    op.drop_index(op.f('ix_resumes_upload_hash'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_id'), table_name='resumes')
    op.drop_table('resumes')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_api_key'), table_name='users')
    op.drop_table('users')

    op.execute('DROP EXTENSION IF EXISTS vector')
