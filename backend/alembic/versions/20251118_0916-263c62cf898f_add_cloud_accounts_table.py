"""add_cloud_accounts_table

Revision ID: 263c62cf898f
Revises: 20512331ba1a
Create Date: 2025-11-18 09:16:26.823236

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '263c62cf898f'
down_revision = '20512331ba1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cloud provider enum type
    cloudprovider_enum = postgresql.ENUM('aws', 'gcp', 'azure', 'alibaba', name='cloudprovider', create_type=False)
    cloudprovider_enum.create(op.get_bind(), checkfirst=True)

    # Create cloud_accounts table
    op.create_table(
        'cloud_accounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('provider', postgresql.ENUM('aws', 'gcp', 'azure', 'alibaba', name='cloudprovider', create_type=False), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('account_name', sa.String(), nullable=True),
        sa.Column('credentials', sa.JSON(), nullable=False),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(), nullable=True),
        sa.Column('sync_error', sa.String(), nullable=True),
        sa.Column('config_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on tenant_id for faster queries
    op.create_index(op.f('ix_cloud_accounts_tenant_id'), 'cloud_accounts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_cloud_accounts_provider'), 'cloud_accounts', ['provider'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_cloud_accounts_provider'), table_name='cloud_accounts')
    op.drop_index(op.f('ix_cloud_accounts_tenant_id'), table_name='cloud_accounts')

    # Drop table
    op.drop_table('cloud_accounts')

    # Drop enum
    op.execute('DROP TYPE cloudprovider')
