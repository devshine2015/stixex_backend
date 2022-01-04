"""create logs table

Revision ID: 79a6b12bae74
Revises: c348dee2ec49
Create Date: 2020-12-09 19:53:09.829398

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79a6b12bae74'
down_revision = 'c348dee2ec49'
branch_labels = None
depends_on = None


def upgrade():
    # op.create_table(
    #     'db_log',
    #     sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    #     sa.Column('log_description', sa.VARCHAR(length=1500)),
    #     sa.Column('network_id', sa.INTEGER),
    #     sa.Column('created', sa.DateTime, default=datetime.utcnow)
    # )
    pass


def downgrade():
    # op.drop_table('db_log')
    pass
