"""Full schema migration - all tables from current models

Revision ID: 001
Revises:
Create Date: 2025-12-13

This migration creates all tables based on current models.py.
Combines all previous migrations into one unified schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # ENUM Types
    # ========================================
    op.execute("CREATE TYPE exitreason AS ENUM ('take_profit', 'stop_loss', 'signal_reverse', 'manual', 'liquidation')")
    op.execute("CREATE TYPE bottype AS ENUM ('ai_trend', 'grid')")
    op.execute("CREATE TYPE gridmode AS ENUM ('arithmetic', 'geometric')")
    op.execute("CREATE TYPE positiondirection AS ENUM ('long', 'short')")
    op.execute("CREATE TYPE gridorderstatus AS ENUM ('pending', 'buy_placed', 'buy_filled', 'sell_placed', 'sell_filled')")
    op.execute("CREATE TYPE tradesource AS ENUM ('manual', 'ai_bot', 'grid_bot')")
    op.execute("CREATE TYPE annotationtype AS ENUM ('note', 'hline', 'vline', 'trendline', 'rectangle', 'price_level')")
    op.execute("CREATE TYPE trenddirection AS ENUM ('long', 'short', 'both')")

    # ========================================
    # Users Table
    # ========================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role', sa.String(), server_default='user', nullable=False),
        sa.Column('exchange', sa.String(), server_default='bitget', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('suspended_at', sa.DateTime(), nullable=True),
        sa.Column('oauth_provider', sa.String(20), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('profile_image', sa.String(500), nullable=True),
        sa.Column('totp_secret', sa.String(), nullable=True),
        sa.Column('is_2fa_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_oauth_id', 'users', ['oauth_id'], unique=False)

    # ========================================
    # API Keys Table
    # ========================================
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('encrypted_secret_key', sa.Text(), nullable=False),
        sa.Column('encrypted_passphrase', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_keys_id', 'api_keys', ['id'], unique=False)

    # ========================================
    # Strategies Table
    # ========================================
    op.create_table(
        'strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.Text(), nullable=True),
        sa.Column('params', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategies_id', 'strategies', ['id'], unique=False)

    # ========================================
    # Grid Bot Templates Table
    # ========================================
    op.create_table(
        'grid_bot_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('direction', postgresql.ENUM('long', 'short', name='positiondirection', create_type=False), nullable=False),
        sa.Column('leverage', sa.Integer(), server_default='5', nullable=False),
        sa.Column('lower_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('upper_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('grid_count', sa.Integer(), nullable=False),
        sa.Column('grid_mode', postgresql.ENUM('arithmetic', 'geometric', name='gridmode', create_type=False), server_default='arithmetic', nullable=False),
        sa.Column('min_investment', sa.Numeric(20, 8), nullable=False),
        sa.Column('recommended_investment', sa.Numeric(20, 8), nullable=True),
        sa.Column('backtest_roi_30d', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_max_drawdown', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_total_trades', sa.Integer(), nullable=True),
        sa.Column('backtest_win_rate', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_roi_history', sa.JSON(), nullable=True),
        sa.Column('backtest_updated_at', sa.DateTime(), nullable=True),
        sa.Column('recommended_period', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('active_users', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_users', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_funds_in_use', sa.Numeric(20, 8), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('upper_price > lower_price', name='check_template_price_range'),
        sa.CheckConstraint('grid_count >= 2 AND grid_count <= 200', name='check_template_grid_count'),
        sa.CheckConstraint('min_investment > 0', name='check_template_min_investment'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_grid_bot_templates_symbol', 'grid_bot_templates', ['symbol'], unique=False)
    op.create_index('ix_grid_bot_templates_is_active', 'grid_bot_templates', ['is_active'], unique=False)
    op.create_index('ix_grid_bot_templates_is_featured', 'grid_bot_templates', ['is_featured'], unique=False)

    # ========================================
    # Trend Bot Templates Table
    # ========================================
    op.create_table(
        'trend_bot_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', sa.String(50), server_default='ema_crossover', nullable=True),
        sa.Column('direction', postgresql.ENUM('long', 'short', 'both', name='trenddirection', create_type=False), server_default='long', nullable=False),
        sa.Column('leverage', sa.Integer(), server_default='5', nullable=False),
        sa.Column('stop_loss_percent', sa.Float(), server_default='2.0', nullable=False),
        sa.Column('take_profit_percent', sa.Float(), server_default='4.0', nullable=False),
        sa.Column('min_investment', sa.Numeric(20, 8), server_default='50.0', nullable=False),
        sa.Column('recommended_investment', sa.Numeric(20, 8), nullable=True),
        sa.Column('backtest_roi_30d', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_win_rate', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_max_drawdown', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_total_trades', sa.Integer(), nullable=True),
        sa.Column('backtest_updated_at', sa.DateTime(), nullable=True),
        sa.Column('recommended_period', sa.String(50), nullable=True),
        sa.Column('risk_level', sa.String(20), server_default='medium', nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('active_users', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_users', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('min_investment > 0', name='check_trend_min_investment'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trend_bot_templates_symbol', 'trend_bot_templates', ['symbol'], unique=False)
    op.create_index('ix_trend_bot_templates_is_active', 'trend_bot_templates', ['is_active'], unique=False)
    op.create_index('ix_trend_bot_templates_is_featured', 'trend_bot_templates', ['is_featured'], unique=False)

    # ========================================
    # Bot Instances Table
    # ========================================
    op.create_table(
        'bot_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bot_type', postgresql.ENUM('ai_trend', 'grid', name='bottype', create_type=False), server_default='ai_trend', nullable=False),
        sa.Column('allocation_percent', sa.Numeric(5, 2), server_default='10.0', nullable=False),
        sa.Column('symbol', sa.String(20), server_default='BTCUSDT', nullable=False),
        sa.Column('max_leverage', sa.Integer(), server_default='10', nullable=False),
        sa.Column('max_positions', sa.Integer(), server_default='3', nullable=False),
        sa.Column('stop_loss_percent', sa.Numeric(5, 2), server_default='5.0', nullable=True),
        sa.Column('take_profit_percent', sa.Numeric(5, 2), server_default='10.0', nullable=True),
        sa.Column('telegram_notify', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_running', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_started_at', sa.DateTime(), nullable=True),
        sa.Column('last_stopped_at', sa.DateTime(), nullable=True),
        sa.Column('last_trade_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('total_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('winning_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_pnl', sa.Numeric(20, 8), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('allocation_percent > 0 AND allocation_percent <= 100', name='check_allocation_range'),
        sa.CheckConstraint('max_leverage >= 1 AND max_leverage <= 100', name='check_bot_leverage_range'),
        sa.CheckConstraint('max_positions >= 1 AND max_positions <= 20', name='check_bot_positions_range'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_id'], ['grid_bot_templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bot_instances_id', 'bot_instances', ['id'], unique=False)
    op.create_index('idx_bot_instances_user_id', 'bot_instances', ['user_id'], unique=False)
    op.create_index('idx_bot_instances_user_running', 'bot_instances', ['user_id', 'is_running'], unique=False)
    op.create_index('idx_bot_instances_type', 'bot_instances', ['bot_type'], unique=False)

    # ========================================
    # Grid Bot Configs Table
    # ========================================
    op.create_table(
        'grid_bot_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_instance_id', sa.Integer(), nullable=False),
        sa.Column('lower_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('upper_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('grid_count', sa.Integer(), server_default='10', nullable=False),
        sa.Column('grid_mode', postgresql.ENUM('arithmetic', 'geometric', name='gridmode', create_type=False), server_default='arithmetic', nullable=False),
        sa.Column('total_investment', sa.Numeric(20, 8), nullable=False),
        sa.Column('per_grid_amount', sa.Numeric(20, 8), nullable=True),
        sa.Column('trigger_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('stop_upper', sa.Numeric(20, 8), nullable=True),
        sa.Column('stop_lower', sa.Numeric(20, 8), nullable=True),
        sa.Column('current_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('active_buy_orders', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active_sell_orders', sa.Integer(), server_default='0', nullable=False),
        sa.Column('filled_buy_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('filled_sell_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('realized_profit', sa.Numeric(20, 8), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('upper_price > lower_price', name='check_price_range'),
        sa.CheckConstraint('grid_count >= 2 AND grid_count <= 100', name='check_grid_count_range'),
        sa.ForeignKeyConstraint(['bot_instance_id'], ['bot_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bot_instance_id')
    )
    op.create_index('ix_grid_bot_configs_id', 'grid_bot_configs', ['id'], unique=False)

    # ========================================
    # Grid Orders Table
    # ========================================
    op.create_table(
        'grid_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grid_config_id', sa.Integer(), nullable=False),
        sa.Column('grid_index', sa.Integer(), nullable=False),
        sa.Column('grid_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('buy_order_id', sa.String(100), nullable=True),
        sa.Column('sell_order_id', sa.String(100), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'buy_placed', 'buy_filled', 'sell_placed', 'sell_filled', name='gridorderstatus', create_type=False), server_default='pending', nullable=False),
        sa.Column('buy_filled_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('buy_filled_qty', sa.Numeric(20, 8), nullable=True),
        sa.Column('buy_filled_at', sa.DateTime(), nullable=True),
        sa.Column('sell_filled_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('sell_filled_qty', sa.Numeric(20, 8), nullable=True),
        sa.Column('sell_filled_at', sa.DateTime(), nullable=True),
        sa.Column('profit', sa.Numeric(20, 8), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['grid_config_id'], ['grid_bot_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_grid_orders_id', 'grid_orders', ['id'], unique=False)
    op.create_index('idx_grid_orders_config', 'grid_orders', ['grid_config_id'], unique=False)
    op.create_index('idx_grid_orders_status', 'grid_orders', ['status'], unique=False)

    # ========================================
    # Bot Status Table (Legacy)
    # ========================================
    op.create_table(
        'bot_status',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('is_running', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id']),
        sa.PrimaryKeyConstraint('user_id')
    )

    # ========================================
    # Bot Config Table (Legacy)
    # ========================================
    op.create_table(
        'bot_config',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('max_risk_percent', sa.Float(), server_default='1.0', nullable=True),
        sa.Column('leverage', sa.Integer(), server_default='5', nullable=True),
        sa.Column('auto_tp', sa.Float(), server_default='3.0', nullable=True),
        sa.Column('auto_sl', sa.Float(), server_default='1.5', nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id')
    )

    # ========================================
    # Trades Table
    # ========================================
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Numeric(18, 8), nullable=False),
        sa.Column('exit_price', sa.Numeric(18, 8), nullable=True),
        sa.Column('pnl', sa.Numeric(18, 8), server_default='0', nullable=True),
        sa.Column('pnl_percent', sa.Float(), server_default='0', nullable=True),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('leverage', sa.Integer(), server_default='1', nullable=True),
        sa.Column('exit_reason', postgresql.ENUM('take_profit', 'stop_loss', 'signal_reverse', 'manual', 'liquidation', name='exitreason', create_type=False), server_default='manual', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('enter_tag', sa.String(100), nullable=True),
        sa.Column('exit_tag', sa.String(100), nullable=True),
        sa.Column('order_tag', sa.String(100), nullable=True),
        sa.Column('bot_instance_id', sa.Integer(), nullable=True),
        sa.Column('trade_source', postgresql.ENUM('manual', 'ai_bot', 'grid_bot', name='tradesource', create_type=False), server_default='manual', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id']),
        sa.ForeignKeyConstraint(['bot_instance_id'], ['bot_instances.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trades_id', 'trades', ['id'], unique=False)
    op.create_index('idx_trade_user_created', 'trades', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_trade_symbol', 'trades', ['symbol'], unique=False)
    op.create_index('idx_trade_strategy', 'trades', ['strategy_id'], unique=False)
    op.create_index('idx_trade_bot_instance', 'trades', ['bot_instance_id'], unique=False)

    # ========================================
    # Positions Table
    # ========================================
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('entry_price', sa.Numeric(18, 8), nullable=False),
        sa.Column('size', sa.Float(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('pnl', sa.Numeric(18, 8), server_default='0', nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('bot_instance_id', sa.Integer(), nullable=True),
        sa.Column('exchange_order_id', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['bot_instance_id'], ['bot_instances.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_positions_id', 'positions', ['id'], unique=False)
    op.create_index('idx_position_bot_instance', 'positions', ['bot_instance_id'], unique=False)
    op.create_index('idx_position_user_symbol', 'positions', ['user_id', 'symbol'], unique=False)

    # ========================================
    # Equities Table
    # ========================================
    op.create_table(
        'equities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.Numeric(18, 8), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_equities_id', 'equities', ['id'], unique=False)
    op.create_index('idx_equity_user_time', 'equities', ['user_id', 'timestamp'], unique=False)

    # ========================================
    # Bot Logs Table
    # ========================================
    op.create_table(
        'bot_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bot_logs_id', 'bot_logs', ['id'], unique=False)
    op.create_index('idx_botlog_user_created', 'bot_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_botlog_event_type', 'bot_logs', ['event_type'], unique=False)

    # ========================================
    # Open Orders Table
    # ========================================
    op.create_table(
        'open_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), server_default='open', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_open_orders_id', 'open_orders', ['id'], unique=False)
    op.create_index('idx_openorder_user_status', 'open_orders', ['user_id', 'status'], unique=False)
    op.create_index('idx_openorder_symbol', 'open_orders', ['symbol'], unique=False)

    # ========================================
    # Backtest Results Table
    # ========================================
    op.create_table(
        'backtest_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pair', sa.String(), nullable=True),
        sa.Column('timeframe', sa.String(), nullable=True),
        sa.Column('initial_balance', sa.Float(), nullable=False),
        sa.Column('final_balance', sa.Float(), nullable=False),
        sa.Column('metrics', sa.Text(), nullable=True),
        sa.Column('equity_curve', sa.Text(), nullable=True),
        sa.Column('params', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='queued', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_results_id', 'backtest_results', ['id'], unique=False)
    op.create_index('ix_backtest_results_user_id', 'backtest_results', ['user_id'], unique=False)
    op.create_index('idx_backtest_user_created', 'backtest_results', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_backtest_status', 'backtest_results', ['status'], unique=False)

    # ========================================
    # Backtest Trades Table
    # ========================================
    op.create_table(
        'backtest_trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.String(), nullable=True),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=True),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('qty', sa.Float(), server_default='1.0', nullable=True),
        sa.Column('fee', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('pnl', sa.Float(), server_default='0.0', nullable=True),
        sa.ForeignKeyConstraint(['result_id'], ['backtest_results.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_trades_id', 'backtest_trades', ['id'], unique=False)

    # ========================================
    # System Alerts Table
    # ========================================
    op.create_table(
        'system_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_alerts_id', 'system_alerts', ['id'], unique=False)
    op.create_index('idx_alert_user_level', 'system_alerts', ['user_id', 'level'], unique=False)
    op.create_index('idx_alert_resolved', 'system_alerts', ['is_resolved'], unique=False)
    op.create_index('idx_alert_created', 'system_alerts', ['created_at'], unique=False)

    # ========================================
    # Risk Settings Table
    # ========================================
    op.create_table(
        'risk_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('daily_loss_limit', sa.Float(), server_default='500.0', nullable=False),
        sa.Column('max_leverage', sa.Integer(), server_default='10', nullable=False),
        sa.Column('max_positions', sa.Integer(), server_default='5', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint('daily_loss_limit > 0', name='check_positive_loss_limit'),
        sa.CheckConstraint('max_leverage >= 1 AND max_leverage <= 100', name='check_leverage_range'),
        sa.CheckConstraint('max_positions >= 1 AND max_positions <= 50', name='check_positions_range'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_risk_settings_id', 'risk_settings', ['id'], unique=False)

    # ========================================
    # User Settings Table
    # ========================================
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_telegram_bot_token', sa.Text(), nullable=True),
        sa.Column('encrypted_telegram_chat_id', sa.Text(), nullable=True),
        sa.Column('telegram_notify_trades', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('telegram_notify_system', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('telegram_notify_errors', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_settings_id', 'user_settings', ['id'], unique=False)

    # ========================================
    # Trading Signals Table
    # ========================================
    op.create_table(
        'trading_signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('signal_type', sa.String(10), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('indicators', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trading_signals_id', 'trading_signals', ['id'], unique=False)
    op.create_index('idx_signal_user_timestamp', 'trading_signals', ['user_id', 'timestamp'], unique=False)
    op.create_index('idx_signal_symbol', 'trading_signals', ['symbol'], unique=False)
    op.create_index('idx_signal_strategy', 'trading_signals', ['strategy_id'], unique=False)
    op.create_index('ix_trading_signals_timestamp', 'trading_signals', ['timestamp'], unique=False)

    # ========================================
    # Chart Annotations Table
    # ========================================
    op.create_table(
        'chart_annotations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('annotation_type', postgresql.ENUM('note', 'hline', 'vline', 'trendline', 'rectangle', 'price_level', name='annotationtype', create_type=False), nullable=False),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('start_timestamp', sa.DateTime(), nullable=True),
        sa.Column('end_timestamp', sa.DateTime(), nullable=True),
        sa.Column('price', sa.Numeric(20, 8), nullable=True),
        sa.Column('start_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('end_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('style', sa.JSON(), nullable=True),
        sa.Column('alert_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('alert_triggered', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('alert_direction', sa.String(10), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_locked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chart_annotations_id', 'chart_annotations', ['id'], unique=False)
    op.create_index('idx_annotation_user_symbol', 'chart_annotations', ['user_id', 'symbol'], unique=False)
    op.create_index('idx_annotation_active', 'chart_annotations', ['user_id', 'is_active'], unique=False)
    op.create_index('idx_annotation_created', 'chart_annotations', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('chart_annotations')
    op.drop_table('trading_signals')
    op.drop_table('user_settings')
    op.drop_table('risk_settings')
    op.drop_table('system_alerts')
    op.drop_table('backtest_trades')
    op.drop_table('backtest_results')
    op.drop_table('open_orders')
    op.drop_table('bot_logs')
    op.drop_table('equities')
    op.drop_table('positions')
    op.drop_table('trades')
    op.drop_table('bot_config')
    op.drop_table('bot_status')
    op.drop_table('grid_orders')
    op.drop_table('grid_bot_configs')
    op.drop_table('bot_instances')
    op.drop_table('trend_bot_templates')
    op.drop_table('grid_bot_templates')
    op.drop_table('strategies')
    op.drop_table('api_keys')
    op.drop_table('users')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS trenddirection")
    op.execute("DROP TYPE IF EXISTS annotationtype")
    op.execute("DROP TYPE IF EXISTS tradesource")
    op.execute("DROP TYPE IF EXISTS gridorderstatus")
    op.execute("DROP TYPE IF EXISTS positiondirection")
    op.execute("DROP TYPE IF EXISTS gridmode")
    op.execute("DROP TYPE IF EXISTS bottype")
    op.execute("DROP TYPE IF EXISTS exitreason")
