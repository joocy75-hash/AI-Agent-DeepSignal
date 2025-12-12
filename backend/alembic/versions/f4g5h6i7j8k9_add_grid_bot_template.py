"""add grid bot template

Revision ID: f4g5h6i7j8k9
Revises: e3f4g5h6i7j8
Create Date: 2025-12-12

관리자가 생성한 그리드봇 템플릿 테이블 추가
- Bitget AI 탭과 유사한 기능
- 백테스트 결과 저장
- 사용자 통계 추적
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "f4g5h6i7j8k9"
down_revision = "e3f4g5h6i7j8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL에서 ENUM 타입이 이미 존재하면 건너뛰기
    conn = op.get_bind()

    # gridmode ENUM 확인 및 생성
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'gridmode'"))
    if not result.fetchone():
        op.execute("CREATE TYPE gridmode AS ENUM ('arithmetic', 'geometric')")

    # positiondirection ENUM 확인 및 생성
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'positiondirection'")
    )
    if not result.fetchone():
        op.execute("CREATE TYPE positiondirection AS ENUM ('long', 'short')")

    # 테이블이 이미 존재하면 건너뛰기
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'grid_bot_templates'"
        )
    )
    if result.fetchone():
        print("Table grid_bot_templates already exists, skipping...")
        return

    # 1. grid_bot_templates 테이블 생성
    op.create_table(
        "grid_bot_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # 기본 정보
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("long", "short", name="positiondirection", create_type=False),
            nullable=False,
        ),
        sa.Column("leverage", sa.Integer(), nullable=False, default=5),
        # 그리드 설정
        sa.Column("lower_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("upper_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("grid_count", sa.Integer(), nullable=False),
        sa.Column(
            "grid_mode",
            sa.Enum("arithmetic", "geometric", name="gridmode", create_type=False),
            nullable=False,
            default="arithmetic",
        ),
        # 투자 제한
        sa.Column("min_investment", sa.Numeric(20, 8), nullable=False),
        sa.Column("recommended_investment", sa.Numeric(20, 8), nullable=True),
        # 백테스트 결과
        sa.Column("backtest_roi_30d", sa.Numeric(10, 4), nullable=True),
        sa.Column("backtest_max_drawdown", sa.Numeric(10, 4), nullable=True),
        sa.Column("backtest_total_trades", sa.Integer(), nullable=True),
        sa.Column("backtest_win_rate", sa.Numeric(10, 4), nullable=True),
        sa.Column("backtest_roi_history", sa.JSON(), nullable=True),
        sa.Column("backtest_updated_at", sa.DateTime(), nullable=True),
        # 추천 정보
        sa.Column("recommended_period", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        # 사용 통계
        sa.Column("active_users", sa.Integer(), nullable=False, default=0),
        sa.Column("total_users", sa.Integer(), nullable=False, default=0),
        sa.Column("total_funds_in_use", sa.Numeric(20, 8), nullable=False, default=0),
        # 상태
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, default=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        # 관리
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "upper_price > lower_price", name="check_template_price_range"
        ),
        sa.CheckConstraint(
            "grid_count >= 2 AND grid_count <= 200", name="check_template_grid_count"
        ),
        sa.CheckConstraint("min_investment > 0", name="check_template_min_investment"),
    )

    # 2. 인덱스 생성
    op.create_index("ix_grid_bot_templates_symbol", "grid_bot_templates", ["symbol"])
    op.create_index(
        "ix_grid_bot_templates_is_active", "grid_bot_templates", ["is_active"]
    )
    op.create_index(
        "ix_grid_bot_templates_is_featured", "grid_bot_templates", ["is_featured"]
    )

    # 3. bot_instances 테이블에 template_id 컬럼 추가 (SQLite batch mode)
    with op.batch_alter_table("bot_instances") as batch_op:
        batch_op.add_column(sa.Column("template_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    # 1. bot_instances에서 template_id 컬럼 제거 (SQLite batch mode)
    with op.batch_alter_table("bot_instances") as batch_op:
        batch_op.drop_column("template_id")

    # 2. 인덱스 삭제
    op.drop_index("ix_grid_bot_templates_is_featured", "grid_bot_templates")
    op.drop_index("ix_grid_bot_templates_is_active", "grid_bot_templates")
    op.drop_index("ix_grid_bot_templates_symbol", "grid_bot_templates")

    # 3. 테이블 삭제
    op.drop_table("grid_bot_templates")

    # 4. Enum 타입 삭제 (PostgreSQL의 경우)
    # op.execute("DROP TYPE IF EXISTS positiondirection")
