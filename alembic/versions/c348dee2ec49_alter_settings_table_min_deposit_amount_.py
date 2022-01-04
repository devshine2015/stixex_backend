"""alter settings table min_deposit_amount field_added

Revision ID: c348dee2ec49
Revises: b5cba3a9b028
Create Date: 2020-12-04 18:29:40.862655

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c348dee2ec49'
down_revision = 'b5cba3a9b028'
branch_labels = None
depends_on = None


def upgrade():
    # op.add_column('app_settings', sa.Column('min_deposit_amount', sa.NUMERIC(), nullable=True))
    pass

def downgrade():
    # op.drop_column('app_settings', 'min_deposit_amount')
    pass
