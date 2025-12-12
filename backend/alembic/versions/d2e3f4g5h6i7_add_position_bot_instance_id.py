"""Add bot_instance_id to positions table

Revision ID: d2e3f4g5h6i7
Revises: c1d2e3f4g5h6
Create Date: 2025-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4g5h6i7'
down_revision: Union[str, None] = 'c1d2e3f4g5h6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Position 테이블에 bot_instance_id, exchange_order_id 컬럼 추가
    with op.batch_alter_table('positions', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('bot_instance_id', sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('exchange_order_id', sa.String(100), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_position_bot_instance',
            'bot_instances',
            ['bot_instance_id'],
            ['id'],
            ondelete='SET NULL'
        )
        batch_op.create_index(
            'idx_position_bot_instance',
            ['bot_instance_id']
        )
        batch_op.create_index(
            'idx_position_user_symbol',
            ['user_id', 'symbol']
        )


def downgrade() -> None:
    with op.batch_alter_table('positions', schema=None) as batch_op:
        batch_op.drop_index('idx_position_user_symbol')
        batch_op.drop_index('idx_position_bot_instance')
        batch_op.drop_constraint('fk_position_bot_instance', type_='foreignkey')
        batch_op.drop_column('exchange_order_id')
        batch_op.drop_column('bot_instance_id')
