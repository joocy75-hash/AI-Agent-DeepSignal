"""add_trade_signal_tags

Revision ID: c4d780a5b3bc
Revises: d2e3f4g5h6i7
Create Date: 2025-12-12 13:54:34.752552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d780a5b3bc'
down_revision: Union[str, None] = 'd2e3f4g5h6i7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 호환: add_column만 사용 (alter_column은 SQLite에서 지원 안함)

    # Trade 테이블에 시그널 태그 컬럼 추가
    with op.batch_alter_table('trades', schema=None) as batch_op:
        batch_op.add_column(sa.Column('enter_tag', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('exit_tag', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('order_tag', sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('trades', schema=None) as batch_op:
        batch_op.drop_column('order_tag')
        batch_op.drop_column('exit_tag')
        batch_op.drop_column('enter_tag')
