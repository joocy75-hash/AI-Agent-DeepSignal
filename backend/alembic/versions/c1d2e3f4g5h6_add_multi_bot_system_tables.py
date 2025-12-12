"""Add multi-bot system tables

다중 봇 시스템을 위한 테이블 추가:
- bot_instances: 봇 인스턴스 관리
- grid_bot_configs: 그리드 봇 설정
- grid_orders: 그리드 주문 추적
- trades 테이블에 bot_instance_id, trade_source 컬럼 추가

관련 문서: docs/MULTI_BOT_01_OVERVIEW.md, MULTI_BOT_02_DATABASE.md

Revision ID: c1d2e3f4g5h6
Revises: b1c2d3e4f5g6
Create Date: 2024-12-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4g5h6"
down_revision: Union[str, None] = "b1c2d3e4f5g6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """다중 봇 시스템 테이블 생성"""

    # 1. Enum 타입 생성 (SQLite는 Enum 지원 안함, VARCHAR로 처리)
    # PostgreSQL 사용 시 아래 주석 해제
    # op.execute("CREATE TYPE bottype AS ENUM ('ai_trend', 'grid')")
    # op.execute("CREATE TYPE gridmode AS ENUM ('arithmetic', 'geometric')")
    # op.execute("CREATE TYPE gridorderstatus AS ENUM ('pending', 'buy_placed', 'buy_filled', 'sell_placed', 'sell_filled')")
    # op.execute("CREATE TYPE tradesource AS ENUM ('manual', 'ai_bot', 'grid_bot')")

    # 2. bot_instances 테이블 생성
    op.create_table(
        "bot_instances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bot_type", sa.String(20), nullable=False, server_default="ai_trend"),
        sa.Column("allocation_percent", sa.Numeric(5, 2), nullable=False, server_default="10.0"),
        sa.Column("symbol", sa.String(20), nullable=False, server_default="BTCUSDT"),
        sa.Column("max_leverage", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_positions", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("stop_loss_percent", sa.Numeric(5, 2), nullable=True, server_default="5.0"),
        sa.Column("take_profit_percent", sa.Numeric(5, 2), nullable=True, server_default="10.0"),
        sa.Column("telegram_notify", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_running", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("last_started_at", sa.DateTime(), nullable=True),
        sa.Column("last_stopped_at", sa.DateTime(), nullable=True),
        sa.Column("last_trade_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("winning_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_pnl", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="SET NULL"),
        sa.CheckConstraint("allocation_percent > 0 AND allocation_percent <= 100", name="check_allocation_range"),
        sa.CheckConstraint("max_leverage >= 1 AND max_leverage <= 100", name="check_bot_leverage_range"),
        sa.CheckConstraint("max_positions >= 1 AND max_positions <= 20", name="check_bot_positions_range"),
    )

    # bot_instances 인덱스 생성
    op.create_index("idx_bot_instances_user_id", "bot_instances", ["user_id"])
    op.create_index("idx_bot_instances_user_running", "bot_instances", ["user_id", "is_running"])
    op.create_index("idx_bot_instances_type", "bot_instances", ["bot_type"])

    # 3. grid_bot_configs 테이블 생성
    op.create_table(
        "grid_bot_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bot_instance_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("lower_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("upper_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("grid_count", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("grid_mode", sa.String(20), nullable=False, server_default="arithmetic"),
        sa.Column("total_investment", sa.Numeric(20, 8), nullable=False),
        sa.Column("per_grid_amount", sa.Numeric(20, 8), nullable=True),
        sa.Column("trigger_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("stop_upper", sa.Numeric(20, 8), nullable=True),
        sa.Column("stop_lower", sa.Numeric(20, 8), nullable=True),
        sa.Column("current_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("active_buy_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_sell_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("filled_buy_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("filled_sell_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("realized_profit", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["bot_instance_id"], ["bot_instances.id"], ondelete="CASCADE"),
        sa.CheckConstraint("upper_price > lower_price", name="check_price_range"),
        sa.CheckConstraint("grid_count >= 2 AND grid_count <= 100", name="check_grid_count_range"),
    )

    # 4. grid_orders 테이블 생성
    op.create_table(
        "grid_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grid_config_id", sa.Integer(), nullable=False),
        sa.Column("grid_index", sa.Integer(), nullable=False),
        sa.Column("grid_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("buy_order_id", sa.String(100), nullable=True),
        sa.Column("sell_order_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("buy_filled_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("buy_filled_qty", sa.Numeric(20, 8), nullable=True),
        sa.Column("buy_filled_at", sa.DateTime(), nullable=True),
        sa.Column("sell_filled_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("sell_filled_qty", sa.Numeric(20, 8), nullable=True),
        sa.Column("sell_filled_at", sa.DateTime(), nullable=True),
        sa.Column("profit", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["grid_config_id"], ["grid_bot_configs.id"], ondelete="CASCADE"),
    )

    # grid_orders 인덱스 생성
    op.create_index("idx_grid_orders_config", "grid_orders", ["grid_config_id"])
    op.create_index("idx_grid_orders_status", "grid_orders", ["status"])

    # 5. trades 테이블에 다중 봇 시스템 컬럼 추가
    # SQLite는 ALTER TABLE로 외래키 추가를 지원하지 않으므로 batch mode 사용
    with op.batch_alter_table("trades", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bot_instance_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("trade_source", sa.String(20), nullable=False, server_default="manual")
        )
        batch_op.create_index("idx_trade_bot_instance", ["bot_instance_id"])
        # SQLite에서는 외래키 제약조건을 나중에 추가할 수 없으므로 인덱스만 생성
        # PostgreSQL 사용 시 아래 주석 해제
        # batch_op.create_foreign_key(
        #     "fk_trades_bot_instance",
        #     "bot_instances",
        #     ["bot_instance_id"],
        #     ["id"],
        #     ondelete="SET NULL"
        # )


def downgrade() -> None:
    """다중 봇 시스템 테이블 제거"""

    # trades 테이블에서 다중 봇 시스템 컬럼 제거 (batch mode for SQLite)
    with op.batch_alter_table("trades", schema=None) as batch_op:
        batch_op.drop_index("idx_trade_bot_instance")
        batch_op.drop_column("trade_source")
        batch_op.drop_column("bot_instance_id")

    # grid_orders 테이블 삭제
    op.drop_index("idx_grid_orders_status", table_name="grid_orders")
    op.drop_index("idx_grid_orders_config", table_name="grid_orders")
    op.drop_table("grid_orders")

    # grid_bot_configs 테이블 삭제
    op.drop_table("grid_bot_configs")

    # bot_instances 테이블 삭제
    op.drop_index("idx_bot_instances_type", table_name="bot_instances")
    op.drop_index("idx_bot_instances_user_running", table_name="bot_instances")
    op.drop_index("idx_bot_instances_user_id", table_name="bot_instances")
    op.drop_table("bot_instances")

    # Enum 타입 삭제 (PostgreSQL 사용 시)
    # op.execute("DROP TYPE IF EXISTS tradesource")
    # op.execute("DROP TYPE IF EXISTS gridorderstatus")
    # op.execute("DROP TYPE IF EXISTS gridmode")
    # op.execute("DROP TYPE IF EXISTS bottype")
