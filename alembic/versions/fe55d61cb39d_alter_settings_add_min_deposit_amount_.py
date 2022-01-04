"""Alter Settings add min_deposit_amount_usdt

Revision ID: fe55d61cb39d
Revises: 79a6b12bae74
Create Date: 2020-12-12 12:20:52.108880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe55d61cb39d'
down_revision = '79a6b12bae74'
branch_labels = None
depends_on = None


def upgrade():
    # op.add_column('app_settings', sa.Column('min_deposit_amount_usdt', sa.NUMERIC(), nullable=True))
    pass

def downgrade():
    # op.drop_column('app_settings', 'min_deposit_amount_usdt')
    pass
