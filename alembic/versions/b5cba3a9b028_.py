"""empty message

Revision ID: b5cba3a9b028
Revises: 85e93286bd1c
Create Date: 2020-10-06 02:19:41.024746

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5cba3a9b028'
down_revision = '85e93286bd1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.alter_column('db_bet', 'amount',
    #            existing_type=sa.BIGINT(),
    #            type_=sa.Numeric(),
    #            existing_nullable=True)
    # op.alter_column('db_bet', 'fee_amount',
    #            existing_type=sa.BIGINT(),
    #            type_=sa.Numeric(),
    #            existing_nullable=True)
    # op.alter_column('db_bet', 'paid_amount',
    #            existing_type=sa.BIGINT(),
    #            type_=sa.Numeric(),
    #            existing_nullable=True)
    # op.alter_column('db_chain_event', 'amount',
    #            existing_type=sa.BIGINT(),
    #            type_=sa.Numeric(),
    #            existing_nullable=True)
    # op.alter_column('db_withdraw', 'amount',
    #            existing_type=sa.BIGINT(),
    #            type_=sa.Numeric(),
    #            existing_nullable=True)
    # ### end Alembic commands ###
    pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.alter_column('db_withdraw', 'amount',
    #            existing_type=sa.Numeric(),
    #            type_=sa.BIGINT(),
    #            existing_nullable=True)
    # op.alter_column('db_chain_event', 'amount',
    #            existing_type=sa.Numeric(),
    #            type_=sa.BIGINT(),
    #            existing_nullable=True)
    # op.alter_column('db_bet', 'paid_amount',
    #            existing_type=sa.Numeric(),
    #            type_=sa.BIGINT(),
    #            existing_nullable=True)
    # op.alter_column('db_bet', 'fee_amount',
    #            existing_type=sa.Numeric(),
    #            type_=sa.BIGINT(),
    #            existing_nullable=True)
    # op.alter_column('db_bet', 'amount',
    #            existing_type=sa.Numeric(),
    #            type_=sa.BIGINT(),
    #            existing_nullable=True)
    # ### end Alembic commands ###
    pass