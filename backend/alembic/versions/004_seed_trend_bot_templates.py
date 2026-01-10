"""Seed initial trend bot templates

Revision ID: 004
Revises: 003
Create Date: 2026-01-10

This migration adds initial TrendBotTemplate data for the multibot system.
"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert initial trend bot templates."""

    # Get the table reference
    trend_bot_templates = sa.table(
        'trend_bot_templates',
        sa.column('name', sa.String),
        sa.column('symbol', sa.String),
        sa.column('description', sa.Text),
        sa.column('strategy_type', sa.String),
        sa.column('direction', sa.String),
        sa.column('leverage', sa.Integer),
        sa.column('stop_loss_percent', sa.Float),
        sa.column('take_profit_percent', sa.Float),
        sa.column('min_investment', sa.Numeric),
        sa.column('recommended_investment', sa.Numeric),
        sa.column('backtest_roi_30d', sa.Numeric),
        sa.column('backtest_win_rate', sa.Numeric),
        sa.column('backtest_max_drawdown', sa.Numeric),
        sa.column('backtest_total_trades', sa.Integer),
        sa.column('recommended_period', sa.String),
        sa.column('risk_level', sa.String),
        sa.column('tags', sa.JSON),
        sa.column('is_active', sa.Boolean),
        sa.column('is_featured', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    now = datetime.utcnow()

    op.bulk_insert(trend_bot_templates, [
        {
            'name': 'ETH AI Fusion',
            'symbol': 'ETHUSDT',
            'description': 'AI 기반 이더리움 추세 추종 전략. EMA, RSI, MACD 조합으로 진입 신호 생성.',
            'strategy_type': 'eth_ai_fusion',
            'direction': 'both',
            'leverage': 10,
            'stop_loss_percent': 1.5,
            'take_profit_percent': 3.0,
            'min_investment': 100,
            'recommended_investment': 500,
            'backtest_roi_30d': 12.5,
            'backtest_win_rate': 62.3,
            'backtest_max_drawdown': 8.2,
            'backtest_total_trades': 48,
            'recommended_period': '7-30 days',
            'risk_level': 'medium',
            'tags': '["ai", "trend", "eth", "recommended"]',
            'is_active': True,
            'is_featured': True,
            'sort_order': 1,
            'created_at': now,
            'updated_at': now,
        },
        {
            'name': 'BTC Momentum',
            'symbol': 'BTCUSDT',
            'description': '비트코인 모멘텀 전략. 강한 추세에서 진입하여 빠른 수익 실현.',
            'strategy_type': 'btc_momentum',
            'direction': 'both',
            'leverage': 5,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
            'min_investment': 100,
            'recommended_investment': 1000,
            'backtest_roi_30d': 8.7,
            'backtest_win_rate': 58.5,
            'backtest_max_drawdown': 6.5,
            'backtest_total_trades': 35,
            'recommended_period': '14-60 days',
            'risk_level': 'low',
            'tags': '["btc", "momentum", "stable"]',
            'is_active': True,
            'is_featured': True,
            'sort_order': 2,
            'created_at': now,
            'updated_at': now,
        },
        {
            'name': 'SOL Scalper',
            'symbol': 'SOLUSDT',
            'description': '솔라나 단타 전략. 높은 변동성을 활용한 빠른 매매.',
            'strategy_type': 'sol_scalper',
            'direction': 'both',
            'leverage': 15,
            'stop_loss_percent': 1.0,
            'take_profit_percent': 2.0,
            'min_investment': 50,
            'recommended_investment': 300,
            'backtest_roi_30d': 18.3,
            'backtest_win_rate': 55.2,
            'backtest_max_drawdown': 12.1,
            'backtest_total_trades': 124,
            'recommended_period': '3-14 days',
            'risk_level': 'high',
            'tags': '["sol", "scalping", "high-frequency"]',
            'is_active': True,
            'is_featured': False,
            'sort_order': 3,
            'created_at': now,
            'updated_at': now,
        },
        {
            'name': 'XRP Swing',
            'symbol': 'XRPUSDT',
            'description': '리플 스윙 전략. 중기 추세를 따라가는 안정적인 매매.',
            'strategy_type': 'xrp_swing',
            'direction': 'long',
            'leverage': 5,
            'stop_loss_percent': 3.0,
            'take_profit_percent': 6.0,
            'min_investment': 50,
            'recommended_investment': 200,
            'backtest_roi_30d': 6.2,
            'backtest_win_rate': 65.0,
            'backtest_max_drawdown': 5.8,
            'backtest_total_trades': 18,
            'recommended_period': '30-90 days',
            'risk_level': 'low',
            'tags': '["xrp", "swing", "conservative"]',
            'is_active': True,
            'is_featured': False,
            'sort_order': 4,
            'created_at': now,
            'updated_at': now,
        },
        {
            'name': 'DOGE Trend',
            'symbol': 'DOGEUSDT',
            'description': '도지코인 추세 전략. 밈코인 특유의 급등락을 활용.',
            'strategy_type': 'doge_trend',
            'direction': 'both',
            'leverage': 10,
            'stop_loss_percent': 2.5,
            'take_profit_percent': 5.0,
            'min_investment': 30,
            'recommended_investment': 150,
            'backtest_roi_30d': 15.8,
            'backtest_win_rate': 52.1,
            'backtest_max_drawdown': 15.5,
            'backtest_total_trades': 67,
            'recommended_period': '7-21 days',
            'risk_level': 'high',
            'tags': '["doge", "meme", "volatile"]',
            'is_active': True,
            'is_featured': False,
            'sort_order': 5,
            'created_at': now,
            'updated_at': now,
        },
    ])


def downgrade() -> None:
    """Remove seeded trend bot templates."""
    op.execute(
        "DELETE FROM trend_bot_templates WHERE strategy_type IN "
        "('eth_ai_fusion', 'btc_momentum', 'sol_scalper', 'xrp_swing', 'doge_trend')"
    )
