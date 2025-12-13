"""Add bot restart tracking fields

Revision ID: 002
Revises: 001
Create Date: 2025-12-14

This migration adds restart tracking fields to bot_status table
to prevent infinite restart loops.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add restart tracking columns to bot_status table
    op.add_column('bot_status', sa.Column('restart_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('bot_status', sa.Column('last_restart_attempt', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove restart tracking columns
    op.drop_column('bot_status', 'last_restart_attempt')
    op.drop_column('bot_status', 'restart_attempts')
