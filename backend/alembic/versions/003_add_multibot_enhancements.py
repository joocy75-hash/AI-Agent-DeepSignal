"""Add multibot system enhancements

Revision ID: 003
Revises: 002
Create Date: 2026-01-10

This migration adds:
- trend_template_id column to bot_instances (FK to trend_bot_templates)
- allocated_amount column to bot_instances (investment amount in USDT)
- current_pnl_percent column to bot_instances (current ROI %)
- last_signal_at column to bot_instances (last signal timestamp)
- user_margin_usage table for caching margin usage per user
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # 1. Add new columns to bot_instances
    # ========================================

    # trend_template_id - FK to trend_bot_templates
    op.add_column('bot_instances', sa.Column(
        'trend_template_id',
        sa.Integer(),
        sa.ForeignKey('trend_bot_templates.id', ondelete='SET NULL'),
        nullable=True
    ))

    # allocated_amount - Investment amount in USDT
    op.add_column('bot_instances', sa.Column(
        'allocated_amount',
        sa.Numeric(15, 2),
        nullable=True,
        server_default='0'
    ))

    # current_pnl_percent - Current ROI percentage
    op.add_column('bot_instances', sa.Column(
        'current_pnl_percent',
        sa.Numeric(10, 4),
        nullable=True,
        server_default='0'
    ))

    # last_signal_at - Last signal timestamp
    op.add_column('bot_instances', sa.Column(
        'last_signal_at',
        sa.DateTime(),
        nullable=True
    ))

    # Add check constraint for allocated_amount
    op.create_check_constraint(
        'check_allocated_amount_positive',
        'bot_instances',
        'allocated_amount >= 0'
    )

    # ========================================
    # 2. Create user_margin_usage table
    # ========================================
    op.create_table(
        'user_margin_usage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('total_balance', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('used_margin', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('available_margin', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('active_bot_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create index for user_margin_usage
    op.create_index('idx_user_margin_usage_user_id', 'user_margin_usage', ['user_id'])


def downgrade() -> None:
    # ========================================
    # 1. Drop user_margin_usage table
    # ========================================
    op.drop_index('idx_user_margin_usage_user_id', table_name='user_margin_usage')
    op.drop_table('user_margin_usage')

    # ========================================
    # 2. Remove columns from bot_instances
    # ========================================
    op.drop_constraint('check_allocated_amount_positive', 'bot_instances', type_='check')
    op.drop_column('bot_instances', 'last_signal_at')
    op.drop_column('bot_instances', 'current_pnl_percent')
    op.drop_column('bot_instances', 'allocated_amount')
    op.drop_column('bot_instances', 'trend_template_id')
