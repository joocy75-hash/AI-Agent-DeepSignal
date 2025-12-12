# 작업 지시서 A: 백엔드 기반 구축

## 📌 담당 영역
- 데이터베이스 모델 생성
- Alembic 마이그레이션
- API 엔드포인트 구현

---

## 1. 사전 요구사항

### 1.1 개발 환경 설정
```bash
cd /Users/mr.joo/Desktop/auto-dashboard/backend
source venv/bin/activate  # 가상환경 활성화
```

### 1.2 필요 파일 위치
```
backend/
├── src/
│   ├── database/
│   │   └── models.py           # 모델 추가할 파일
│   ├── schemas/
│   │   └── grid_template_schema.py  # 새로 생성
│   ├── api/
│   │   ├── admin_grid_template.py   # 새로 생성 (관리자 API)
│   │   └── grid_template.py         # 새로 생성 (사용자 API)
│   └── services/
│       └── grid_template_service.py # 새로 생성
├── alembic/
│   └── versions/
│       └── xxxx_add_grid_bot_template.py  # 새로 생성
```

---

## 2. 작업 1: 데이터베이스 모델 생성

### 2.1 파일: `backend/src/database/models.py`

#### Step 1: Enum 추가 (기존 Enum 영역에)

```python
# 파일 상단 Enum 정의 영역에 추가

class PositionDirection(str, Enum):
    """포지션 방향"""
    LONG = "long"
    SHORT = "short"
```

#### Step 2: GridBotTemplate 모델 추가

```python
# GridBotConfig 클래스 위에 추가

class GridBotTemplate(Base):
    """
    관리자가 생성한 그리드봇 템플릿
    - 백테스트 결과와 함께 저장
    - 일반 사용자가 "Use" 버튼으로 복사하여 사용
    """
    __tablename__ = "grid_bot_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ===== 기본 정보 =====
    name = Column(String(100), nullable=False)           # 템플릿 이름
    symbol = Column(String(20), nullable=False)          # "SOLUSDT", "BTCUSDT"
    direction = Column(Enum(PositionDirection), nullable=False)  # LONG, SHORT
    leverage = Column(Integer, default=5)                # 기본 레버리지

    # ===== 그리드 설정 =====
    lower_price = Column(Numeric(20, 8), nullable=False)  # 하단 가격
    upper_price = Column(Numeric(20, 8), nullable=False)  # 상단 가격
    grid_count = Column(Integer, nullable=False)          # 그리드 개수 (2-200)
    grid_mode = Column(
        Enum(GridMode),
        default=GridMode.ARITHMETIC,
        nullable=False
    )  # ARITHMETIC or GEOMETRIC

    # ===== 투자 제한 =====
    min_investment = Column(Numeric(20, 8), nullable=False)      # 최소 투자금액 (USDT)
    recommended_investment = Column(Numeric(20, 8), nullable=True)  # 권장 투자금액

    # ===== 백테스트 결과 =====
    backtest_roi_30d = Column(Numeric(10, 4), nullable=True)     # 30일 ROI (%)
    backtest_max_drawdown = Column(Numeric(10, 4), nullable=True)  # 최대 낙폭 (%)
    backtest_total_trades = Column(Integer, nullable=True)        # 총 거래 수
    backtest_win_rate = Column(Numeric(10, 4), nullable=True)    # 승률 (%)
    backtest_roi_history = Column(JSON, nullable=True)           # 일별 ROI 배열 (차트용)
    backtest_updated_at = Column(DateTime, nullable=True)        # 백테스트 실행 시각

    # ===== 추천 정보 =====
    recommended_period = Column(String(50), nullable=True)       # "7-30 days"
    description = Column(Text, nullable=True)                    # 봇 설명
    tags = Column(JSON, nullable=True)                           # ["stable", "high-risk"] 등

    # ===== 사용 통계 =====
    active_users = Column(Integer, default=0)                    # 현재 사용 중인 유저 수
    total_users = Column(Integer, default=0)                     # 누적 사용자 수
    total_funds_in_use = Column(Numeric(20, 8), default=0)       # 총 운용 자금 (USDT)

    # ===== 상태 =====
    is_active = Column(Boolean, default=True)                    # 공개 여부
    is_featured = Column(Boolean, default=False)                 # 추천 표시 (상단 노출)
    sort_order = Column(Integer, default=0)                      # 정렬 순서

    # ===== 관리 =====
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # ===== 관계 =====
    creator = relationship("User", foreign_keys=[created_by])
    instances = relationship("BotInstance", back_populates="template")

    def __repr__(self):
        return f"<GridBotTemplate {self.symbol} {self.direction.value} {self.leverage}x>"
```

#### Step 3: BotInstance 모델 수정

```python
# BotInstance 클래스에 아래 필드 추가

class BotInstance(Base):
    # ... 기존 필드들 ...

    # 추가: 템플릿 참조 (grid 타입인 경우)
    template_id = Column(
        Integer,
        ForeignKey("grid_bot_templates.id"),
        nullable=True
    )

    # 관계 추가
    template = relationship("GridBotTemplate", back_populates="instances")
```

### 2.2 검증 체크리스트
- [ ] PositionDirection Enum 추가됨
- [ ] GridBotTemplate 모델 추가됨
- [ ] BotInstance에 template_id 필드 추가됨
- [ ] 관계(relationship) 양방향 설정됨

---

## 3. 작업 2: Alembic 마이그레이션

### 3.1 마이그레이션 파일 생성

```bash
cd /Users/mr.joo/Desktop/auto-dashboard/backend

# 환경변수 설정
export DATABASE_URL="sqlite+aiosqlite:///./trading.db"
export ENCRYPTION_KEY="Dz9w_blEMa-tMD5hqK6V7yiaYecQBdsTaO0PJR3ESn8="

# 마이그레이션 생성
alembic revision -m "add_grid_bot_template"
```

### 3.2 마이그레이션 파일 작성

생성된 파일 (`alembic/versions/xxxx_add_grid_bot_template.py`)을 아래처럼 작성:

```python
"""add grid bot template

Revision ID: [자동생성]
Revises: [이전 revision]
Create Date: [자동생성]
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '[자동생성ID]'
down_revision = '[이전revision]'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. grid_bot_templates 테이블 생성
    op.create_table(
        'grid_bot_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        # 기본 정보
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('direction', sa.Enum('long', 'short', name='positiondirection'), nullable=False),
        sa.Column('leverage', sa.Integer(), default=5),

        # 그리드 설정
        sa.Column('lower_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('upper_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('grid_count', sa.Integer(), nullable=False),
        sa.Column('grid_mode', sa.Enum('ARITHMETIC', 'GEOMETRIC', name='gridmode'), default='ARITHMETIC'),

        # 투자 제한
        sa.Column('min_investment', sa.Numeric(20, 8), nullable=False),
        sa.Column('recommended_investment', sa.Numeric(20, 8), nullable=True),

        # 백테스트 결과
        sa.Column('backtest_roi_30d', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_max_drawdown', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_total_trades', sa.Integer(), nullable=True),
        sa.Column('backtest_win_rate', sa.Numeric(10, 4), nullable=True),
        sa.Column('backtest_roi_history', sa.JSON(), nullable=True),
        sa.Column('backtest_updated_at', sa.DateTime(), nullable=True),

        # 추천 정보
        sa.Column('recommended_period', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),

        # 사용 통계
        sa.Column('active_users', sa.Integer(), default=0),
        sa.Column('total_users', sa.Integer(), default=0),
        sa.Column('total_funds_in_use', sa.Numeric(20, 8), default=0),

        # 상태
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('sort_order', sa.Integer(), default=0),

        # 관리
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),

        sa.PrimaryKeyConstraint('id')
    )

    # 2. 인덱스 생성
    op.create_index('ix_grid_bot_templates_symbol', 'grid_bot_templates', ['symbol'])
    op.create_index('ix_grid_bot_templates_is_active', 'grid_bot_templates', ['is_active'])
    op.create_index('ix_grid_bot_templates_is_featured', 'grid_bot_templates', ['is_featured'])

    # 3. bot_instances 테이블에 template_id 컬럼 추가
    op.add_column(
        'bot_instances',
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('grid_bot_templates.id'), nullable=True)
    )


def downgrade() -> None:
    # 1. bot_instances에서 template_id 컬럼 제거
    op.drop_column('bot_instances', 'template_id')

    # 2. 인덱스 삭제
    op.drop_index('ix_grid_bot_templates_is_featured', 'grid_bot_templates')
    op.drop_index('ix_grid_bot_templates_is_active', 'grid_bot_templates')
    op.drop_index('ix_grid_bot_templates_symbol', 'grid_bot_templates')

    # 3. 테이블 삭제
    op.drop_table('grid_bot_templates')
```

### 3.3 마이그레이션 실행

```bash
# 마이그레이션 적용
alembic upgrade head

# 확인
alembic current
```

### 3.4 검증 체크리스트
- [ ] 마이그레이션 파일 생성됨
- [ ] upgrade() 함수 작성됨
- [ ] downgrade() 함수 작성됨
- [ ] `alembic upgrade head` 성공
- [ ] DB에 grid_bot_templates 테이블 생성됨
- [ ] bot_instances에 template_id 컬럼 추가됨

---

## 4. 작업 3: Pydantic 스키마 생성

### 4.1 파일: `backend/src/schemas/grid_template_schema.py` (새로 생성)

```python
"""
Grid Bot Template Schemas
- 관리자 템플릿 CRUD용 스키마
- 사용자 조회/사용용 스키마
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, validator

from src.database.models import GridMode, PositionDirection


# ===== 기본 스키마 =====

class GridTemplateBase(BaseModel):
    """템플릿 기본 필드"""
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=3, max_length=20)
    direction: PositionDirection
    leverage: int = Field(default=5, ge=1, le=125)

    lower_price: Decimal = Field(..., gt=0)
    upper_price: Decimal = Field(..., gt=0)
    grid_count: int = Field(..., ge=2, le=200)
    grid_mode: GridMode = GridMode.ARITHMETIC

    min_investment: Decimal = Field(..., gt=0)
    recommended_investment: Optional[Decimal] = None

    recommended_period: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

    @validator('upper_price')
    def upper_must_be_greater_than_lower(cls, v, values):
        if 'lower_price' in values and v <= values['lower_price']:
            raise ValueError('upper_price must be greater than lower_price')
        return v

    @validator('symbol')
    def symbol_must_be_uppercase(cls, v):
        return v.upper()


# ===== 관리자용 스키마 =====

class GridTemplateCreate(GridTemplateBase):
    """템플릿 생성 요청 (관리자)"""
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0


class GridTemplateUpdate(BaseModel):
    """템플릿 수정 요청 (관리자)"""
    name: Optional[str] = None
    lower_price: Optional[Decimal] = None
    upper_price: Optional[Decimal] = None
    grid_count: Optional[int] = None
    grid_mode: Optional[GridMode] = None
    leverage: Optional[int] = None

    min_investment: Optional[Decimal] = None
    recommended_investment: Optional[Decimal] = None

    recommended_period: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = None


class BacktestResult(BaseModel):
    """백테스트 결과"""
    roi_30d: Decimal                  # 30일 ROI %
    max_drawdown: Decimal             # 최대 낙폭 %
    total_trades: int                 # 총 거래 수
    win_rate: Decimal                 # 승률 %
    roi_history: List[float]          # 일별 ROI 배열 (30개)

    class Config:
        from_attributes = True


# ===== 사용자용 스키마 =====

class GridTemplateListItem(BaseModel):
    """템플릿 목록 아이템 (사용자)"""
    id: int
    name: str
    symbol: str
    direction: PositionDirection
    leverage: int

    # 백테스트 결과
    backtest_roi_30d: Optional[Decimal] = None
    backtest_max_drawdown: Optional[Decimal] = None
    roi_chart: Optional[List[float]] = None  # roi_history를 차트용으로 변환

    # 추천 정보
    recommended_period: Optional[str] = None
    min_investment: Decimal

    # 통계
    active_users: int = 0
    total_funds_in_use: Decimal = Decimal('0')

    # 상태
    is_featured: bool = False

    class Config:
        from_attributes = True


class GridTemplateDetail(GridTemplateListItem):
    """템플릿 상세 정보 (사용자)"""
    # 추가 필드
    upper_price: Decimal
    lower_price: Decimal
    grid_count: int
    grid_mode: GridMode
    recommended_investment: Optional[Decimal] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

    backtest_total_trades: Optional[int] = None
    backtest_win_rate: Optional[Decimal] = None
    backtest_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UseTemplateRequest(BaseModel):
    """템플릿 사용 요청 (봇 생성)"""
    investment_amount: Decimal = Field(..., gt=0)
    leverage: Optional[int] = Field(default=None, ge=1, le=125)  # None이면 템플릿 기본값

    @validator('investment_amount')
    def validate_investment(cls, v):
        if v < 5:  # 최소 $5
            raise ValueError('Minimum investment is $5')
        return v


class UseTemplateResponse(BaseModel):
    """템플릿 사용 응답 (생성된 봇 정보)"""
    bot_instance_id: int
    grid_config_id: int
    message: str = "Bot created successfully from template"


# ===== 관리자 응답용 =====

class GridTemplateAdminDetail(GridTemplateDetail):
    """관리자용 상세 정보"""
    is_active: bool
    sort_order: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_users: int = 0

    class Config:
        from_attributes = True


# ===== 응답 래퍼 =====

class GridTemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    success: bool = True
    data: List[GridTemplateListItem]
    total: int


class GridTemplateDetailResponse(BaseModel):
    """템플릿 상세 응답"""
    success: bool = True
    data: GridTemplateDetail
```

### 4.2 검증 체크리스트
- [ ] grid_template_schema.py 파일 생성됨
- [ ] 모든 import 정상 동작
- [ ] Validator 함수들 정상 동작
- [ ] Config.from_attributes = True 설정됨

---

## 5. 작업 4: 서비스 레이어 생성

### 5.1 파일: `backend/src/services/grid_template_service.py` (새로 생성)

```python
"""
Grid Template Service
- 템플릿 CRUD
- 통계 업데이트
"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    GridBotTemplate,
    BotInstance,
    GridBotConfig,
    GridOrder,
    User,
    BotType,
    GridMode
)
from src.schemas.grid_template_schema import (
    GridTemplateCreate,
    GridTemplateUpdate,
    UseTemplateRequest
)


class GridTemplateService:
    """그리드 템플릿 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ===== 조회 =====

    async def get_active_templates(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[GridBotTemplate]:
        """
        활성화된 템플릿 목록 조회 (사용자용)
        - is_active=True인 것만
        - is_featured 우선, sort_order 순
        """
        query = (
            select(GridBotTemplate)
            .where(GridBotTemplate.is_active == True)
            .order_by(
                GridBotTemplate.is_featured.desc(),
                GridBotTemplate.sort_order.asc(),
                GridBotTemplate.backtest_roi_30d.desc().nullslast()
            )
            .offset(offset)
            .limit(limit)
        )

        if symbol:
            query = query.where(GridBotTemplate.symbol == symbol.upper())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_template_by_id(self, template_id: int) -> Optional[GridBotTemplate]:
        """템플릿 ID로 조회"""
        result = await self.db.execute(
            select(GridBotTemplate).where(GridBotTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_all_templates(
        self,
        include_inactive: bool = False
    ) -> List[GridBotTemplate]:
        """모든 템플릿 조회 (관리자용)"""
        query = select(GridBotTemplate).order_by(
            GridBotTemplate.sort_order.asc(),
            GridBotTemplate.created_at.desc()
        )

        if not include_inactive:
            query = query.where(GridBotTemplate.is_active == True)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ===== 생성/수정/삭제 =====

    async def create_template(
        self,
        data: GridTemplateCreate,
        created_by: int
    ) -> GridBotTemplate:
        """템플릿 생성 (관리자)"""
        template = GridBotTemplate(
            **data.dict(),
            created_by=created_by
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self,
        template_id: int,
        data: GridTemplateUpdate
    ) -> Optional[GridBotTemplate]:
        """템플릿 수정 (관리자)"""
        template = await self.get_template_by_id(template_id)
        if not template:
            return None

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: int) -> bool:
        """템플릿 삭제 (관리자) - 실제 삭제가 아닌 비활성화"""
        template = await self.get_template_by_id(template_id)
        if not template:
            return False

        template.is_active = False
        await self.db.commit()
        return True

    async def toggle_template(self, template_id: int) -> Optional[GridBotTemplate]:
        """템플릿 공개/비공개 토글"""
        template = await self.get_template_by_id(template_id)
        if not template:
            return None

        template.is_active = not template.is_active
        await self.db.commit()
        await self.db.refresh(template)
        return template

    # ===== 템플릿 사용 (봇 생성) =====

    async def use_template(
        self,
        template_id: int,
        user_id: int,
        request: UseTemplateRequest
    ) -> tuple[BotInstance, GridBotConfig]:
        """
        템플릿으로 봇 인스턴스 생성

        1. 템플릿 조회
        2. 최소 투자금액 검증
        3. BotInstance 생성
        4. GridBotConfig 생성 (템플릿 설정 복사)
        5. GridOrder 레코드 생성
        6. 템플릿 통계 업데이트
        """
        # 1. 템플릿 조회
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        if not template.is_active:
            raise ValueError("This template is not available")

        # 2. 최소 투자금액 검증
        if request.investment_amount < template.min_investment:
            raise ValueError(
                f"Minimum investment is {template.min_investment} USDT"
            )

        # 레버리지 결정 (요청값 or 템플릿 기본값)
        leverage = request.leverage or template.leverage

        # 3. BotInstance 생성
        bot_instance = BotInstance(
            user_id=user_id,
            name=f"{template.symbol} Grid ({template.direction.value})",
            bot_type=BotType.GRID,
            symbol=template.symbol,
            max_leverage=leverage,
            template_id=template.id,
            is_active=True,
            is_running=False
        )
        self.db.add(bot_instance)
        await self.db.flush()  # ID 할당

        # 4. GridBotConfig 생성
        per_grid_amount = self._calculate_per_grid_amount(
            request.investment_amount,
            template.grid_count,
            leverage
        )

        grid_config = GridBotConfig(
            bot_instance_id=bot_instance.id,
            lower_price=template.lower_price,
            upper_price=template.upper_price,
            grid_count=template.grid_count,
            grid_mode=template.grid_mode,
            total_investment=request.investment_amount,
            per_grid_amount=per_grid_amount
        )
        self.db.add(grid_config)
        await self.db.flush()

        # 5. GridOrder 레코드 생성
        grid_prices = self._calculate_grid_prices(
            template.lower_price,
            template.upper_price,
            template.grid_count,
            template.grid_mode
        )

        for idx, price in enumerate(grid_prices):
            grid_order = GridOrder(
                grid_config_id=grid_config.id,
                grid_index=idx,
                grid_price=price
            )
            self.db.add(grid_order)

        # 6. 템플릿 통계 업데이트
        template.active_users += 1
        template.total_users += 1
        template.total_funds_in_use += request.investment_amount

        await self.db.commit()
        await self.db.refresh(bot_instance)
        await self.db.refresh(grid_config)

        return bot_instance, grid_config

    # ===== 통계 업데이트 =====

    async def decrement_active_user(
        self,
        template_id: int,
        investment_amount: Decimal
    ):
        """봇 종료 시 활성 사용자 감소"""
        template = await self.get_template_by_id(template_id)
        if template and template.active_users > 0:
            template.active_users -= 1
            template.total_funds_in_use -= investment_amount
            if template.total_funds_in_use < 0:
                template.total_funds_in_use = Decimal('0')
            await self.db.commit()

    # ===== 백테스트 결과 저장 =====

    async def save_backtest_result(
        self,
        template_id: int,
        roi_30d: Decimal,
        max_drawdown: Decimal,
        total_trades: int,
        win_rate: Decimal,
        roi_history: List[float]
    ) -> Optional[GridBotTemplate]:
        """백테스트 결과 저장"""
        from datetime import datetime

        template = await self.get_template_by_id(template_id)
        if not template:
            return None

        template.backtest_roi_30d = roi_30d
        template.backtest_max_drawdown = max_drawdown
        template.backtest_total_trades = total_trades
        template.backtest_win_rate = win_rate
        template.backtest_roi_history = roi_history
        template.backtest_updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(template)
        return template

    # ===== Helper 함수 =====

    def _calculate_per_grid_amount(
        self,
        total_investment: Decimal,
        grid_count: int,
        leverage: int
    ) -> Decimal:
        """그리드당 투자금액 계산"""
        return (total_investment * leverage) / grid_count

    def _calculate_grid_prices(
        self,
        lower_price: Decimal,
        upper_price: Decimal,
        grid_count: int,
        grid_mode: GridMode
    ) -> List[Decimal]:
        """그리드 가격 배열 계산"""
        prices = []

        if grid_mode == GridMode.ARITHMETIC:
            # 등차 방식
            step = (upper_price - lower_price) / (grid_count - 1)
            for i in range(grid_count):
                prices.append(lower_price + (step * i))
        else:
            # 등비 방식
            import math
            ratio = math.pow(float(upper_price / lower_price), 1 / (grid_count - 1))
            for i in range(grid_count):
                prices.append(lower_price * Decimal(str(pow(ratio, i))))

        return prices
```

### 5.2 검증 체크리스트
- [ ] grid_template_service.py 파일 생성됨
- [ ] 모든 CRUD 메서드 구현됨
- [ ] use_template 메서드 구현됨
- [ ] 통계 업데이트 메서드 구현됨

---

## 6. 작업 5: 사용자 API 엔드포인트

### 6.1 파일: `backend/src/api/grid_template.py` (새로 생성)

```python
"""
Grid Template API - 사용자용
- 템플릿 목록 조회
- 템플릿 상세 조회
- 템플릿으로 봇 생성
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.api.dependencies import get_current_user
from src.database.models import User
from src.services.grid_template_service import GridTemplateService
from src.schemas.grid_template_schema import (
    GridTemplateListItem,
    GridTemplateListResponse,
    GridTemplateDetail,
    GridTemplateDetailResponse,
    UseTemplateRequest,
    UseTemplateResponse
)

router = APIRouter(
    prefix="/grid-templates",
    tags=["Grid Templates"]
)


@router.get("", response_model=GridTemplateListResponse)
async def list_templates(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTCUSDT)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    공개된 그리드봇 템플릿 목록 조회

    - AI 탭에 표시될 템플릿들
    - is_featured 템플릿이 상단에 표시
    - ROI 높은 순으로 정렬
    """
    service = GridTemplateService(db)
    templates = await service.get_active_templates(
        symbol=symbol,
        limit=limit,
        offset=offset
    )

    items = []
    for t in templates:
        items.append(GridTemplateListItem(
            id=t.id,
            name=t.name,
            symbol=t.symbol,
            direction=t.direction,
            leverage=t.leverage,
            backtest_roi_30d=t.backtest_roi_30d,
            backtest_max_drawdown=t.backtest_max_drawdown,
            roi_chart=t.backtest_roi_history[-30:] if t.backtest_roi_history else None,
            recommended_period=t.recommended_period,
            min_investment=t.min_investment,
            active_users=t.active_users,
            total_funds_in_use=t.total_funds_in_use,
            is_featured=t.is_featured
        ))

    return GridTemplateListResponse(
        success=True,
        data=items,
        total=len(items)
    )


@router.get("/{template_id}", response_model=GridTemplateDetailResponse)
async def get_template_detail(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    템플릿 상세 정보 조회

    - 그리드 설정 상세
    - 백테스트 결과 상세
    - 사용자가 "Use" 전에 확인하는 정보
    """
    service = GridTemplateService(db)
    template = await service.get_template_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if not template.is_active:
        raise HTTPException(status_code=404, detail="Template is not available")

    return GridTemplateDetailResponse(
        success=True,
        data=GridTemplateDetail(
            id=template.id,
            name=template.name,
            symbol=template.symbol,
            direction=template.direction,
            leverage=template.leverage,
            lower_price=template.lower_price,
            upper_price=template.upper_price,
            grid_count=template.grid_count,
            grid_mode=template.grid_mode,
            min_investment=template.min_investment,
            recommended_investment=template.recommended_investment,
            backtest_roi_30d=template.backtest_roi_30d,
            backtest_max_drawdown=template.backtest_max_drawdown,
            backtest_total_trades=template.backtest_total_trades,
            backtest_win_rate=template.backtest_win_rate,
            backtest_updated_at=template.backtest_updated_at,
            roi_chart=template.backtest_roi_history[-30:] if template.backtest_roi_history else None,
            recommended_period=template.recommended_period,
            description=template.description,
            tags=template.tags,
            active_users=template.active_users,
            total_funds_in_use=template.total_funds_in_use,
            is_featured=template.is_featured
        )
    )


@router.post("/{template_id}/use", response_model=UseTemplateResponse)
async def use_template(
    template_id: int,
    request: UseTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    템플릿으로 그리드봇 생성

    - 투자 금액과 레버리지만 입력
    - 나머지 설정은 템플릿에서 복사
    - 생성 후 바로 시작 가능한 상태

    Request:
    - investment_amount: 투자할 금액 (USDT)
    - leverage: 레버리지 (선택, 미입력시 템플릿 기본값)
    """
    service = GridTemplateService(db)

    try:
        bot_instance, grid_config = await service.use_template(
            template_id=template_id,
            user_id=current_user.id,
            request=request
        )

        return UseTemplateResponse(
            bot_instance_id=bot_instance.id,
            grid_config_id=grid_config.id,
            message=f"Grid bot created from template. Ready to start!"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {str(e)}")
```

### 6.2 라우터 등록

`backend/src/api/__init__.py` 또는 메인 앱 파일에 라우터 추가:

```python
from src.api.grid_template import router as grid_template_router

# app.include_router(...) 영역에 추가
app.include_router(grid_template_router)
```

### 6.3 검증 체크리스트
- [ ] grid_template.py 파일 생성됨
- [ ] GET /grid-templates 엔드포인트 동작
- [ ] GET /grid-templates/{id} 엔드포인트 동작
- [ ] POST /grid-templates/{id}/use 엔드포인트 동작
- [ ] 라우터 등록됨

---

## 7. 작업 6: 관리자 API 엔드포인트

### 7.1 파일: `backend/src/api/admin_grid_template.py` (새로 생성)

```python
"""
Grid Template Admin API - 관리자용
- 템플릿 CRUD
- 공개/비공개 전환
- 백테스트 실행 트리거
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.api.dependencies import get_current_user, require_admin
from src.database.models import User
from src.services.grid_template_service import GridTemplateService
from src.schemas.grid_template_schema import (
    GridTemplateCreate,
    GridTemplateUpdate,
    GridTemplateAdminDetail,
    BacktestResult
)

router = APIRouter(
    prefix="/admin/grid-templates",
    tags=["Admin - Grid Templates"],
    dependencies=[Depends(require_admin)]  # 관리자만 접근 가능
)


@router.get("", response_model=List[GridTemplateAdminDetail])
async def list_all_templates(
    include_inactive: bool = Query(False, description="Include inactive templates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """모든 템플릿 조회 (관리자)"""
    service = GridTemplateService(db)
    templates = await service.get_all_templates(include_inactive=include_inactive)

    return [
        GridTemplateAdminDetail(
            id=t.id,
            name=t.name,
            symbol=t.symbol,
            direction=t.direction,
            leverage=t.leverage,
            lower_price=t.lower_price,
            upper_price=t.upper_price,
            grid_count=t.grid_count,
            grid_mode=t.grid_mode,
            min_investment=t.min_investment,
            recommended_investment=t.recommended_investment,
            backtest_roi_30d=t.backtest_roi_30d,
            backtest_max_drawdown=t.backtest_max_drawdown,
            backtest_total_trades=t.backtest_total_trades,
            backtest_win_rate=t.backtest_win_rate,
            backtest_updated_at=t.backtest_updated_at,
            roi_chart=t.backtest_roi_history[-30:] if t.backtest_roi_history else None,
            recommended_period=t.recommended_period,
            description=t.description,
            tags=t.tags,
            active_users=t.active_users,
            total_users=t.total_users,
            total_funds_in_use=t.total_funds_in_use,
            is_featured=t.is_featured,
            is_active=t.is_active,
            sort_order=t.sort_order,
            created_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in templates
    ]


@router.post("", response_model=GridTemplateAdminDetail)
async def create_template(
    data: GridTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """새 템플릿 생성 (관리자)"""
    service = GridTemplateService(db)
    template = await service.create_template(
        data=data,
        created_by=current_user.id
    )

    return GridTemplateAdminDetail.from_orm(template)


@router.put("/{template_id}", response_model=GridTemplateAdminDetail)
async def update_template(
    template_id: int,
    data: GridTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 수정 (관리자)"""
    service = GridTemplateService(db)
    template = await service.update_template(template_id, data)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return GridTemplateAdminDetail.from_orm(template)


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 삭제 (비활성화)"""
    service = GridTemplateService(db)
    success = await service.delete_template(template_id)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"success": True, "message": "Template deactivated"}


@router.patch("/{template_id}/toggle")
async def toggle_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 공개/비공개 전환"""
    service = GridTemplateService(db)
    template = await service.toggle_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "success": True,
        "is_active": template.is_active,
        "message": f"Template {'activated' if template.is_active else 'deactivated'}"
    }


@router.post("/{template_id}/backtest")
async def run_backtest(
    template_id: int,
    days: int = Query(30, ge=7, le=90, description="Backtest period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    백테스트 실행 (관리자)

    - 백테스트 서비스 호출 (Task B에서 구현)
    - 결과를 템플릿에 저장
    """
    service = GridTemplateService(db)
    template = await service.get_template_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # TODO: 백테스트 서비스 호출 (Task B에서 구현)
    # from src.services.grid_backtester import GridBacktester
    # backtester = GridBacktester()
    # result = await backtester.run(...)

    # 임시 응답 (백테스트 구현 전)
    return {
        "success": True,
        "message": "Backtest queued. Results will be available shortly.",
        "template_id": template_id,
        "days": days
    }
```

### 7.2 라우터 등록

```python
from src.api.admin_grid_template import router as admin_grid_template_router

app.include_router(admin_grid_template_router)
```

### 7.3 검증 체크리스트
- [ ] admin_grid_template.py 파일 생성됨
- [ ] 관리자 권한 검증 동작
- [ ] CRUD 엔드포인트 모두 동작
- [ ] 라우터 등록됨

---

## 8. 테스트 방법

### 8.1 API 테스트 스크립트

```bash
# 1. 서버 시작
cd /Users/mr.joo/Desktop/auto-dashboard/backend
uvicorn src.main:app --reload --port 8000

# 2. 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"admin"}' | jq -r '.access_token')

# 3. 관리자: 템플릿 생성
curl -X POST http://localhost:8000/admin/grid-templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SOL Short Grid",
    "symbol": "SOLUSDT",
    "direction": "short",
    "leverage": 5,
    "lower_price": "120.0",
    "upper_price": "150.0",
    "grid_count": 30,
    "grid_mode": "ARITHMETIC",
    "min_investment": "384.21",
    "recommended_period": "7-30 days",
    "description": "AI recommended grid for SOL futures short position"
  }'

# 4. 사용자: 템플릿 목록 조회
curl -X GET http://localhost:8000/grid-templates \
  -H "Authorization: Bearer $TOKEN"

# 5. 사용자: 템플릿으로 봇 생성
curl -X POST http://localhost:8000/grid-templates/1/use \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "investment_amount": "500.0",
    "leverage": 5
  }'
```

---

## 9. 완료 체크리스트

### Phase A 완료 조건
- [ ] GridBotTemplate 모델 생성 완료
- [ ] Alembic 마이그레이션 성공
- [ ] Pydantic 스키마 작성 완료
- [ ] GridTemplateService 구현 완료
- [ ] 사용자 API 엔드포인트 구현 완료
- [ ] 관리자 API 엔드포인트 구현 완료
- [ ] 라우터 등록 완료
- [ ] API 테스트 통과

---

## 10. 다음 단계

- **Task B (백테스트)**: `GridBacktester` 서비스 구현
- **Task C (프론트엔드)**: UI 컴포넌트 구현
- **Task D (관리자 페이지)**: 관리 UI 구현
