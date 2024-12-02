"""initialize_liquidity_pools

Revision ID: e9d0ff9dab41
Revises: 3f880aad1dbb
Create Date: 2024-12-01 17:21:26.362159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column
from spherepay import config


# revision identifiers, used by Alembic.
revision: str = 'e9d0ff9dab41'
down_revision: Union[str, None] = '3f880aad1dbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Define table structure for raw SQL
    liquidity_pools = table('liquidity_pools',
        column('currency', sa.String),
        column('balance', sa.Numeric),
        column('reserved_balance', sa.Numeric)
    )

    # Insert initial pool balances
    op.bulk_insert(
        liquidity_pools,
        [
            {
                "currency": currency,
                "balance": balance,
                "reserved_balance": 0
            }
            for currency, balance in config.INITIAL_BALANCES.items()
        ]
    )

def downgrade():
    op.execute("DELETE FROM liquidity_pools")
    