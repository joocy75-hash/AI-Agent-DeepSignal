"""add_chart_annotations_table

Revision ID: e3f4g5h6i7j8
Revises: c4d780a5b3bc
Create Date: 2025-12-12 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f4g5h6i7j8'
down_revision: Union[str, None] = 'c4d780a5b3bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # chart_annotations 테이블 생성
    op.create_table(
        'chart_annotations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('annotation_type', sa.Enum(
            'note', 'hline', 'vline', 'trendline', 'rectangle', 'price_level',
            name='annotationtype'
        ), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('start_timestamp', sa.DateTime(), nullable=True),
        sa.Column('end_timestamp', sa.DateTime(), nullable=True),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('start_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('end_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('style', sa.JSON(), nullable=True),
        sa.Column('alert_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('alert_triggered', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('alert_direction', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 인덱스 생성
    op.create_index('idx_annotation_user_symbol', 'chart_annotations', ['user_id', 'symbol'])
    op.create_index('idx_annotation_active', 'chart_annotations', ['user_id', 'is_active'])
    op.create_index('idx_annotation_created', 'chart_annotations', ['created_at'])


def downgrade() -> None:
    # 인덱스 삭제
    op.drop_index('idx_annotation_created', table_name='chart_annotations')
    op.drop_index('idx_annotation_active', table_name='chart_annotations')
    op.drop_index('idx_annotation_user_symbol', table_name='chart_annotations')

    # 테이블 삭제
    op.drop_table('chart_annotations')

    # Enum 타입 삭제 (PostgreSQL의 경우)
    op.execute("DROP TYPE IF EXISTS annotationtype")
