"""create initial tables

Revision ID: 3f880aad1dbb
Revises: 
Create Date: 2024-11-29 19:27:18.975269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f880aad1dbb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Liquidity pools table
    op.create_table(
        'liquidity_pools',
        sa.Column('currency', sa.String(3), primary_key=True),
        sa.Column('balance', sa.Numeric(20, 6), nullable=False),
        sa.Column('reserved_balance', sa.Numeric(20, 6), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # FX rates table
    op.create_table(
        'fx_rates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('currency_pair', sa.String(7), nullable=False),
        sa.Column('rate', sa.Numeric(20, 6), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False)
    )

    # Transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_currency', sa.String(3), nullable=False),
        sa.Column('target_currency', sa.String(3), nullable=False),
        sa.Column('source_amount', sa.Numeric(20, 6), nullable=False),
        sa.Column('target_amount', sa.Numeric(20, 6), nullable=False),
        sa.Column('fx_rate', sa.Numeric(20, 6), nullable=False),
        sa.Column('margin', sa.Numeric(20, 6), nullable=False),
        sa.Column('revenue', sa.Numeric(20, 6), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    op.drop_table('transactions')
    op.drop_table('fx_rates')
    op.drop_table('liquidity_pools')
