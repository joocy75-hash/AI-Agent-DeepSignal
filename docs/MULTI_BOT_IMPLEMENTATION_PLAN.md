# 멀티봇 트레이딩 시스템 구현 계획서

> **버전**: 2.0.0
> **작성일**: 2026-01-10
> **상태**: 🚀 진행 중
> **최종 수정**: 2026-01-10 (v2.0 - 단순화)

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [현재 상태 vs 목표 상태](#현재-상태-vs-목표-상태)
3. [아키텍처 설계](#아키텍처-설계)
4. [Phase 1: 데이터베이스 스키마](#phase-1-데이터베이스-스키마)
5. [Phase 2: 백엔드 API](#phase-2-백엔드-api)
6. [Phase 3: 봇 러너 수정](#phase-3-봇-러너-수정)
7. [Phase 4: 프론트엔드 UI](#phase-4-프론트엔드-ui)
8. [Phase 5: 테스트 및 배포](#phase-5-테스트-및-배포)
9. [리스크 관리 정책](#리스크-관리-정책)
10. [작업 체크리스트](#작업-체크리스트)

---

## v2.0 변경사항 (2026-01-10)

### 주요 변경

| 항목 | 기존 (v1) | 변경 (v2) |
|------|-----------|-----------|
| **마진 한도** | 40% 강제 | 잔고 초과만 체크 |
| **최대 봇 개수** | 10개 | 5개 |
| **전략 템플릿** | `StrategyTemplate` 신규 | `TrendBotTemplate` 활용 (기존 모델) |
| **단일 봇 시스템** | 레거시 호환 유지 | 폐지 (멀티봇 전용) |

---

## 프로젝트 개요

### 목표
사용자가 여러 개의 전략 봇을 동시에 운용할 수 있는 멀티봇 트레이딩 시스템 구현

### 핵심 기능
- 전략별 카드 UI로 한눈에 확인
- 사용자는 금액만 입력하면 즉시 봇 시작
- 각 봇별 독립적인 수익률 추적
- **잔고 초과만 체크** (40% 한도 없음)

### 예상 소요 기간
- Phase 1-2: 백엔드 기초 (1-2일)
- Phase 3: 봇 러너 수정 (2-3일)
- Phase 4: 프론트엔드 (2-3일)
- Phase 5: 테스트/배포 (1일)

---

## 현재 상태 vs 목표 상태

### 현재 상태
```
┌─────────────────────────────────────┐
│ 사용자 → 1개 전략 선택 → 1개 봇 실행 │
│                                     │
│ • 단일 봇만 운용 가능               │
│ • 전략 변경 시 기존 봇 중지 필요    │
│ • 분산 투자 불가                    │
└─────────────────────────────────────┘
```

### 목표 상태
```
┌─────────────────────────────────────────────────────┐
│ 사용자 → N개 전략 카드 중 선택 → N개 봇 동시 실행  │
│                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│ │ ETH Bot  │ │ BTC Bot  │ │ SOL Bot  │  ...        │
│ │ +12.5%   │ │ +8.2%    │ │ -2.1%    │             │
│ │ $500     │ │ $300     │ │ $200     │             │
│ └──────────┘ └──────────┘ └──────────┘             │
│                                                     │
│ 총 사용: $1000 / $2500 (잔고 기준 - 한도 없음)     │
│ 최대 봇: 5개                                        │
└─────────────────────────────────────────────────────┘
```

---

## 아키텍처 설계

### 시스템 흐름도
```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ StrategyCard│  │ StrategyCard│  │ StrategyCard│          │
│  │  (ETH Bot)  │  │  (BTC Bot)  │  │  (SOL Bot)  │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │   MultiBotDashboard   │                       │
│              │   (전체 현황 요약)     │                       │
│              └───────────┬───────────┘                       │
└──────────────────────────┼───────────────────────────────────┘
                           │ REST API
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                        │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    API Layer                             │ │
│  │  /api/v1/multibot/templates    GET    전략 카드 목록    │ │
│  │  /api/v1/multibot/start         POST   봇 시작          │ │
│  │  /api/v1/multibot/stop/{id}     POST   봇 중지          │ │
│  │  /api/v1/multibot/status        GET    전체 봇 상태     │ │
│  │  /api/v1/multibot/balance-check GET    잔고 확인        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Service Layer                           │ │
│  │                                                          │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │ │
│  │  │ MultiBotManager  │  │      BalanceController       │ │ │
│  │  │                  │  │                              │ │ │
│  │  │ • 봇 생성/삭제   │  │ • 전체 잔고 조회            │ │ │
│  │  │ • 상태 관리      │  │ • 사용 중인 금액 계산       │ │ │
│  │  │ • 수익률 집계    │  │ • 잔고 초과만 체크          │ │ │
│  │  └────────┬─────────┘  └──────────────────────────────┘ │ │
│  │           │                                              │ │
│  │           ▼                                              │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │              BotRunner (멀티봇 전용)              │   │ │
│  │  │                                                   │   │ │
│  │  │  • 멀티 인스턴스 동시 실행                       │   │ │
│  │  │  • 인스턴스별 독립 루프                          │   │ │
│  │  │  • 공유 WebSocket 연결                           │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Database Layer                          │ │
│  │                                                          │ │
│  │  trend_bot_templates  기존 AI 추세 봇 템플릿 (활용)     │ │
│  │  bot_instances        실행 중인 봇 (N개/사용자)         │ │
│  │  bot_trades           봇별 거래 기록                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 데이터 흐름
```
1. 사용자가 전략 카드 확인
   Frontend → GET /multibot/templates → TrendBotTemplate 목록 반환

2. 봇 시작 요청
   Frontend → POST /multibot/start {template_id, amount}
   ↓
   BalanceController.check_available(user_id, amount)
   ↓ (잔고 초과 시 거부)
   MultiBotManager.create_bot(user_id, template_id, amount)
   ↓
   BotRunner.start_instance(bot_instance_id)

3. 실시간 상태 업데이트
   BotRunner → bot_instances 테이블 업데이트
   ↓
   Frontend ← GET /multibot/status (폴링 or WebSocket)
```

---

## Phase 1: 데이터베이스 스키마

### 1.1 기존 테이블 활용: TrendBotTemplate

> **중요**: `StrategyTemplate` 신규 생성 불필요. 기존 `TrendBotTemplate` 활용

```python
# 기존 모델 (backend/src/database/models.py)
class TrendBotTemplate(Base):
    __tablename__ = "trend_bot_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), default="ema_crossover")
    direction = Column(SQLEnum(TrendDirection), default=TrendDirection.LONG)
    leverage = Column(Integer, default=5)
    stop_loss_percent = Column(Float, default=2.0)
    take_profit_percent = Column(Float, default=4.0)
    min_investment = Column(Numeric(20, 8), default=50.0)
    max_investment = Column(Numeric(20, 8), default=10000.0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    # ... 기타 필드
```

### 1.2 테이블 수정: bot_instances

```sql
-- 기존 테이블 수정 (ALTER)
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS template_id INT REFERENCES trend_bot_templates(id);
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS allocated_amount DECIMAL(15,2);
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS current_pnl DECIMAL(15,2) DEFAULT 0;
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS current_pnl_percent DECIMAL(10,4) DEFAULT 0;
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS total_trades INT DEFAULT 0;
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS winning_trades INT DEFAULT 0;
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS last_signal_at TIMESTAMP;
ALTER TABLE bot_instances ADD COLUMN IF NOT EXISTS error_message TEXT;

-- 복합 인덱스 (사용자별 활성 봇 조회 최적화)
CREATE INDEX idx_bot_instances_user_active ON bot_instances(user_id, status) WHERE status = 'running';
```

### 1.3 Alembic 마이그레이션 파일

**파일**: `backend/alembic/versions/xxxx_add_multibot_columns.py`

```python
"""Add multibot columns to bot_instances

Revision ID: multibot_001
Revises: previous_revision
Create Date: 2026-01-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'multibot_001'
down_revision = 'previous_revision'  # 실제 값으로 교체

def upgrade():
    # bot_instances 컬럼 추가
    op.add_column('bot_instances', sa.Column('template_id', sa.Integer(), sa.ForeignKey('trend_bot_templates.id')))
    op.add_column('bot_instances', sa.Column('allocated_amount', sa.Numeric(15, 2)))
    op.add_column('bot_instances', sa.Column('current_pnl', sa.Numeric(15, 2), server_default='0'))
    op.add_column('bot_instances', sa.Column('current_pnl_percent', sa.Numeric(10, 4), server_default='0'))
    op.add_column('bot_instances', sa.Column('total_trades', sa.Integer(), server_default='0'))
    op.add_column('bot_instances', sa.Column('winning_trades', sa.Integer(), server_default='0'))
    op.add_column('bot_instances', sa.Column('last_signal_at', sa.DateTime()))
    op.add_column('bot_instances', sa.Column('error_message', sa.Text()))

def downgrade():
    op.drop_column('bot_instances', 'error_message')
    op.drop_column('bot_instances', 'last_signal_at')
    op.drop_column('bot_instances', 'winning_trades')
    op.drop_column('bot_instances', 'total_trades')
    op.drop_column('bot_instances', 'current_pnl_percent')
    op.drop_column('bot_instances', 'current_pnl')
    op.drop_column('bot_instances', 'allocated_amount')
    op.drop_column('bot_instances', 'template_id')
```

---

## Phase 2: 백엔드 API

### 2.1 API 엔드포인트 설계

| 메서드 | 경로 | 설명 | 요청 | 응답 |
|--------|------|------|------|------|
| GET | `/api/v1/multibot/templates` | 전략 카드 목록 | - | TrendBotTemplate[] |
| GET | `/api/v1/multibot/templates/{id}` | 전략 상세 | - | TrendBotTemplate |
| POST | `/api/v1/multibot/bots` | 봇 시작 | {template_id, amount} | BotInstance |
| DELETE | `/api/v1/multibot/bots/{id}` | 봇 중지 | - | {success: bool} |
| GET | `/api/v1/multibot/bots` | 내 봇 목록 | - | BotInstance[] |
| GET | `/api/v1/multibot/bots/{id}` | 봇 상세 | - | BotInstance |
| GET | `/api/v1/multibot/summary` | 전체 요약 | - | BalanceSummary |
| GET | `/api/v1/multibot/balance-check` | 잔고 확인 | ?amount=500 | {available: bool} |

### 2.2 Pydantic 스키마

**파일**: `backend/src/schemas/multibot_schema.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class TemplateResponse(BaseModel):
    """전략 카드 응답 (TrendBotTemplate 기반)"""
    id: int
    name: str
    symbol: str
    description: Optional[str]

    # 거래 설정
    strategy_type: str
    direction: str  # "long" / "short"
    leverage: int

    # 리스크 설정
    stop_loss_percent: float
    take_profit_percent: float

    # 투자 한도
    min_investment: float
    max_investment: float

    # 상태
    is_active: bool
    is_featured: bool

    class Config:
        from_attributes = True


class BotStartRequest(BaseModel):
    """봇 시작 요청"""
    template_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0, le=100000)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v < 10:
            raise ValueError("최소 투자금은 $10입니다")
        return round(v, 2)


class BotInstanceResponse(BaseModel):
    """봇 인스턴스 응답"""
    id: int
    template_id: int
    template_name: str

    # 거래 정보
    symbol: str
    leverage: int

    # 투자 정보
    allocated_amount: float
    current_pnl: float
    current_pnl_percent: float

    # 상태
    status: str  # running/stopped/error
    error_message: Optional[str]

    # 통계
    total_trades: int
    winning_trades: int
    win_rate: float

    # 현재 포지션 (있는 경우)
    current_position: Optional[dict]

    # 시간
    started_at: datetime
    last_signal_at: Optional[datetime]

    class Config:
        from_attributes = True


class BalanceSummaryResponse(BaseModel):
    """잔고 요약 응답"""
    total_balance: float           # 총 잔고
    used_amount: float             # 사용 중인 금액
    available_amount: float        # 사용 가능 금액

    active_bot_count: int
    max_bot_count: int  # 5개
    total_pnl: float
    total_pnl_percent: float

    bots: List[BotInstanceResponse]


class BalanceCheckResponse(BaseModel):
    """잔고 확인 응답"""
    requested_amount: float
    available: bool
    current_balance: float
    used_amount: float
    remaining: float
    message: str
```

### 2.3 서비스 레이어

**파일**: `backend/src/services/balance_controller.py`

```python
"""
잔고 컨트롤러

사용자별 잔고 조회 및 가용 금액 확인
- 40% 한도 폐지
- 잔고 초과만 체크
"""
import logging
from typing import Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import BotInstance

logger = logging.getLogger(__name__)


class BalanceController:
    """잔고 컨트롤러"""

    MAX_BOTS_PER_USER = 5  # 사용자당 최대 봇 수

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_can_start(
        self,
        user_id: int,
        amount: float
    ) -> Tuple[bool, str]:
        """
        봇 시작 가능 여부 확인

        Returns:
            (가능 여부, 메시지)
        """
        balance_info = await self.get_user_balance(user_id)

        # 잔고 초과 체크 (40% 한도 없음)
        if balance_info.used_amount + amount > balance_info.total_balance:
            remaining = balance_info.total_balance - balance_info.used_amount
            return (
                False,
                f"잔고가 부족합니다 (사용 가능: ${remaining:.2f})"
            )

        return (True, "OK")

    async def check_balance(
        self,
        user_id: int,
        amount: float
    ):
        """잔고 확인 (API용)"""
        from ..schemas.multibot_schema import BalanceCheckResponse

        balance_info = await self.get_user_balance(user_id)

        remaining = balance_info.total_balance - balance_info.used_amount
        available = amount <= remaining

        message = "사용 가능합니다" if available else "잔고가 부족합니다"

        return BalanceCheckResponse(
            requested_amount=amount,
            available=available,
            current_balance=balance_info.total_balance,
            used_amount=balance_info.used_amount,
            remaining=remaining,
            message=message
        )

    async def get_user_balance(self, user_id: int):
        """
        사용자 잔고 정보 조회

        거래소 API + DB에서 현재 잔고 및 사용량 계산
        """
        # 1. 거래소에서 총 잔고 조회
        total_balance = await self._get_exchange_balance(user_id)

        # 2. 활성 봇들의 할당 금액 합계
        result = await self.db.execute(
            select(BotInstance).where(
                and_(
                    BotInstance.user_id == user_id,
                    BotInstance.status == "running"
                )
            )
        )
        active_bots = result.scalars().all()
        used_amount = sum(float(b.allocated_amount or 0) for b in active_bots)

        # 간단한 데이터 클래스 반환
        class BalanceInfo:
            pass

        info = BalanceInfo()
        info.total_balance = total_balance
        info.used_amount = used_amount
        info.available_amount = max(0, total_balance - used_amount)
        info.active_bot_count = len(active_bots)

        return info

    async def _get_exchange_balance(self, user_id: int) -> float:
        """거래소에서 USDT 잔고 조회"""
        try:
            from .exchange_service import ExchangeService

            client, _ = await ExchangeService.get_user_exchange_client(self.db, user_id)
            if not client:
                logger.warning(f"User {user_id} has no exchange client")
                return 0

            balance = await client.get_futures_balance()
            return float(balance.get("USDT", {}).get("total", 0))

        except Exception as e:
            logger.error(f"Failed to get balance for user {user_id}: {e}")
            return 0
```

**파일**: `backend/src/services/multibot_manager.py`

```python
"""
멀티봇 매니저 서비스

여러 봇 인스턴스의 생성, 관리, 모니터링을 담당
- 기존 TrendBotTemplate 활용
- 최대 5개 봇 제한
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TrendBotTemplate, BotInstance
from ..schemas.multibot_schema import (
    TemplateResponse,
    BotInstanceResponse,
    BalanceSummaryResponse,
)

logger = logging.getLogger(__name__)


class MultiBotManager:
    """멀티봇 관리자"""

    MAX_BOTS_PER_USER = 5  # 사용자당 최대 봇 수

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_templates(self) -> List[TemplateResponse]:
        """활성화된 전략 템플릿 목록 조회"""
        result = await self.db.execute(
            select(TrendBotTemplate)
            .where(TrendBotTemplate.is_active == True)
            .order_by(TrendBotTemplate.is_featured.desc(), TrendBotTemplate.id)
        )
        templates = result.scalars().all()
        return [TemplateResponse.model_validate(t) for t in templates]

    async def get_template(self, template_id: int) -> Optional[TemplateResponse]:
        """전략 템플릿 상세 조회"""
        result = await self.db.execute(
            select(TrendBotTemplate).where(TrendBotTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        return TemplateResponse.model_validate(template) if template else None

    async def start_bot(
        self,
        user_id: int,
        template_id: int,
        amount: float
    ) -> BotInstanceResponse:
        """새 봇 인스턴스 시작"""
        # 1. 템플릿 확인
        template = await self.db.get(TrendBotTemplate, template_id)
        if not template or not template.is_active:
            raise ValueError("유효하지 않은 전략입니다")

        # 2. 금액 범위 확인
        if amount < float(template.min_investment):
            raise ValueError(f"최소 투자금은 ${template.min_investment}입니다")
        if amount > float(template.max_investment):
            raise ValueError(f"최대 투자금은 ${template.max_investment}입니다")

        # 3. 사용자 봇 개수 확인
        active_count = await self._get_active_bot_count(user_id)
        if active_count >= self.MAX_BOTS_PER_USER:
            raise ValueError(f"최대 {self.MAX_BOTS_PER_USER}개의 봇만 운용할 수 있습니다")

        # 4. 동일 심볼 봇 중복 확인
        existing = await self._get_bot_by_symbol(user_id, template.symbol)
        if existing:
            raise ValueError(f"{template.symbol} 봇이 이미 실행 중입니다")

        # 5. 봇 인스턴스 생성
        bot_instance = BotInstance(
            user_id=user_id,
            template_id=template_id,
            symbol=template.symbol,
            status="running",
            allocated_amount=amount,
            current_pnl=0,
            current_pnl_percent=0,
            total_trades=0,
            winning_trades=0,
        )

        self.db.add(bot_instance)
        await self.db.commit()
        await self.db.refresh(bot_instance)

        logger.info(f"Bot started: user={user_id}, template={template.name}, amount=${amount}")

        # 6. BotRunner에 시작 요청 (비동기)
        from .bot_runner import BotRunner
        await BotRunner.start_instance(bot_instance.id)

        return await self._to_response(bot_instance, template)

    async def stop_bot(self, user_id: int, bot_id: int) -> bool:
        """봇 중지"""
        result = await self.db.execute(
            select(BotInstance).where(
                and_(
                    BotInstance.id == bot_id,
                    BotInstance.user_id == user_id,
                    BotInstance.status == "running"
                )
            )
        )
        bot = result.scalar_one_or_none()

        if not bot:
            return False

        # BotRunner에 중지 요청
        from .bot_runner import BotRunner
        await BotRunner.stop_instance(bot_id)

        # DB 상태 업데이트
        bot.status = "stopped"
        await self.db.commit()

        logger.info(f"Bot stopped: user={user_id}, bot_id={bot_id}")
        return True

    async def get_user_bots(
        self,
        user_id: int,
        status_filter: Optional[str] = None
    ) -> List[BotInstanceResponse]:
        """사용자 봇 목록 조회"""
        query = select(BotInstance).where(BotInstance.user_id == user_id)

        if status_filter and status_filter != "all":
            query = query.where(BotInstance.status == status_filter)

        query = query.order_by(BotInstance.created_at.desc())

        result = await self.db.execute(query)
        bots = result.scalars().all()

        responses = []
        for bot in bots:
            template = await self.db.get(TrendBotTemplate, bot.template_id)
            responses.append(await self._to_response(bot, template))

        return responses

    async def get_bot(self, user_id: int, bot_id: int) -> Optional[BotInstanceResponse]:
        """봇 상세 조회"""
        result = await self.db.execute(
            select(BotInstance).where(
                and_(BotInstance.id == bot_id, BotInstance.user_id == user_id)
            )
        )
        bot = result.scalar_one_or_none()

        if not bot:
            return None

        template = await self.db.get(TrendBotTemplate, bot.template_id)
        return await self._to_response(bot, template)

    async def get_user_summary(self, user_id: int) -> BalanceSummaryResponse:
        """사용자 전체 현황 요약"""
        from .balance_controller import BalanceController
        balance_ctrl = BalanceController(self.db)
        balance_info = await balance_ctrl.get_user_balance(user_id)

        # 봇 목록
        bots = await self.get_user_bots(user_id, status_filter="running")

        # 집계
        total_pnl = sum(b.current_pnl for b in bots)

        return BalanceSummaryResponse(
            total_balance=balance_info.total_balance,
            used_amount=balance_info.used_amount,
            available_amount=balance_info.available_amount,
            active_bot_count=len(bots),
            max_bot_count=self.MAX_BOTS_PER_USER,
            total_pnl=total_pnl,
            total_pnl_percent=(total_pnl / balance_info.used_amount * 100) if balance_info.used_amount > 0 else 0,
            bots=bots
        )

    async def _get_active_bot_count(self, user_id: int) -> int:
        """활성 봇 개수 조회"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(BotInstance.id)).where(
                and_(
                    BotInstance.user_id == user_id,
                    BotInstance.status == "running"
                )
            )
        )
        return result.scalar() or 0

    async def _get_bot_by_symbol(self, user_id: int, symbol: str) -> Optional[BotInstance]:
        """심볼로 활성 봇 조회"""
        result = await self.db.execute(
            select(BotInstance).where(
                and_(
                    BotInstance.user_id == user_id,
                    BotInstance.symbol == symbol,
                    BotInstance.status == "running"
                )
            )
        )
        return result.scalar_one_or_none()

    async def _to_response(
        self,
        bot: BotInstance,
        template: Optional[TrendBotTemplate]
    ) -> BotInstanceResponse:
        """BotInstance → Response 변환"""
        win_rate = 0
        if bot.total_trades and bot.total_trades > 0:
            win_rate = ((bot.winning_trades or 0) / bot.total_trades) * 100

        return BotInstanceResponse(
            id=bot.id,
            template_id=bot.template_id or 0,
            template_name=template.name if template else "Unknown",
            symbol=bot.symbol,
            leverage=template.leverage if template else 10,
            allocated_amount=float(bot.allocated_amount or 0),
            current_pnl=float(bot.current_pnl or 0),
            current_pnl_percent=float(bot.current_pnl_percent or 0),
            status=bot.status,
            error_message=bot.error_message,
            total_trades=bot.total_trades or 0,
            winning_trades=bot.winning_trades or 0,
            win_rate=win_rate,
            current_position=None,  # BotRunner에서 조회
            started_at=bot.created_at,
            last_signal_at=bot.last_signal_at,
        )
```

---

## Phase 3: 봇 러너 수정

### 3.1 BotRunner 멀티 인스턴스 지원

**수정 파일**: `backend/src/services/bot_runner.py`

**핵심 변경 사항**:

```python
# 멀티 인스턴스 전용 (단일 봇 폐지)
class BotRunner:
    _instances: dict[int, 'BotRunner'] = {}  # bot_id → runner

    @classmethod
    async def start_instance(cls, bot_instance_id: int):
        """특정 봇 인스턴스 시작"""
        if bot_instance_id in cls._instances:
            return  # 이미 실행 중

        runner = cls(bot_instance_id)
        cls._instances[bot_instance_id] = runner
        asyncio.create_task(runner.run())

    @classmethod
    async def stop_instance(cls, bot_instance_id: int):
        """특정 봇 인스턴스 중지"""
        if bot_instance_id in cls._instances:
            runner = cls._instances[bot_instance_id]
            runner.running = False
            del cls._instances[bot_instance_id]

    async def run(self):
        """개별 봇 루프"""
        while self.running:
            try:
                await self._execute_strategy_cycle()
                await asyncio.sleep(self.interval)
            except Exception as e:
                await self._handle_error(e)
```

### 3.2 WebSocket 공유

```python
class SharedWebSocketManager:
    """
    모든 봇이 공유하는 WebSocket 연결 관리자

    심볼별로 하나의 연결만 유지하여 API 호출 최소화
    """
    _connections: dict[str, WebSocketClient] = {}
    _subscribers: dict[str, set[int]] = {}  # symbol → {bot_id, ...}

    @classmethod
    async def subscribe(cls, symbol: str, bot_id: int, callback):
        """봇이 심볼 구독"""
        if symbol not in cls._connections:
            cls._connections[symbol] = await cls._create_connection(symbol)

        cls._subscribers.setdefault(symbol, set()).add(bot_id)
        cls._connections[symbol].add_callback(bot_id, callback)

    @classmethod
    async def unsubscribe(cls, symbol: str, bot_id: int):
        """봇이 심볼 구독 해제"""
        if symbol in cls._subscribers:
            cls._subscribers[symbol].discard(bot_id)

            # 마지막 구독자면 연결 종료
            if not cls._subscribers[symbol]:
                await cls._connections[symbol].close()
                del cls._connections[symbol]
                del cls._subscribers[symbol]
```

---

## Phase 4: 프론트엔드 UI

### 4.1 컴포넌트 구조

```
frontend/src/
├── pages/
│   └── MultiBotPage.tsx         # 메인 페이지
├── components/
│   └── multibot/
│       ├── StrategyCard.tsx      # 전략 카드
│       ├── StrategyCardList.tsx  # 카드 그리드
│       ├── BotStatusCard.tsx     # 실행 중 봇 카드
│       ├── ActiveBotsList.tsx    # 내 봇 목록
│       ├── BalanceSummary.tsx    # 잔고 요약 바
│       ├── BotStartModal.tsx     # 봇 시작 모달
│       └── BotDetailModal.tsx    # 봇 상세 모달
├── hooks/
│   └── useMultiBot.ts            # API 훅
└── types/
    └── multibot.ts               # 타입 정의
```

### 4.2 BalanceSummary 컴포넌트

```tsx
// frontend/src/components/multibot/BalanceSummary.tsx

interface BalanceSummaryProps {
  summary: BalanceSummaryResponse;
}

export const BalanceSummary: React.FC<BalanceSummaryProps> = ({ summary }) => {
  const usagePercent = (summary.used_amount / summary.total_balance) * 100;

  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-6">
      <div className="flex justify-between items-center mb-2">
        <span className="text-gray-400">잔고 사용량</span>
        <span className="text-white">
          ${summary.used_amount.toFixed(2)} / ${summary.total_balance.toFixed(2)}
        </span>
      </div>

      {/* 프로그레스 바 */}
      <div className="relative h-4 bg-gray-700 rounded overflow-hidden">
        <div
          className="absolute h-full transition-all bg-blue-500"
          style={{ width: `${Math.min(usagePercent, 100)}%` }}
        />
      </div>

      <div className="flex justify-between mt-2 text-sm">
        <span className="text-gray-400">
          {usagePercent.toFixed(1)}% 사용 중
        </span>
        <span className="text-gray-400">
          가용: ${summary.available_amount.toFixed(2)}
        </span>
      </div>

      {/* 요약 통계 */}
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-700">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">
            {summary.active_bot_count}/{summary.max_bot_count}
          </div>
          <div className="text-sm text-gray-400">활성 봇</div>
        </div>
        <div className="text-center">
          <div className={`text-2xl font-bold ${
            summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl.toFixed(2)}
          </div>
          <div className="text-sm text-gray-400">총 수익</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-400">
            ${summary.available_amount.toFixed(2)}
          </div>
          <div className="text-sm text-gray-400">가용 잔고</div>
        </div>
      </div>
    </div>
  );
};
```

---

## Phase 5: 테스트 및 배포

### 5.1 테스트 케이스

| 카테고리 | 테스트 | 예상 결과 |
|---------|--------|----------|
| 잔고 검증 | 잔고 초과 시도 | 거부 + 에러 메시지 |
| 잔고 검증 | 잔고 범위 내 | 허용 |
| 잔고 검증 | 잔고 0일 때 | 거부 |
| 봇 시작 | 유효한 요청 | 봇 생성 + 실행 |
| 봇 시작 | 동일 심볼 중복 | 거부 |
| 봇 시작 | 최대 개수(5개) 초과 | 거부 |
| 봇 중지 | 실행 중 봇 | 정상 중지 |
| 봇 중지 | 포지션 있을 때 | 포지션 청산 후 중지 |
| UI | 카드 표시 | 올바른 정보 |
| UI | 실시간 업데이트 | 5초마다 갱신 |

### 5.2 배포 체크리스트

```bash
# 1. 로컬 테스트
cd backend
python -m pytest tests/ -v

# 2. 마이그레이션 테스트
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 3. 프론트엔드 빌드
cd frontend
npm run build

# 4. 배포
git add .
git commit -m "feat: Add multi-bot trading system (v2)"
git push hetzner main

# 5. 검증
curl https://api.deepsignal.shop/api/v1/multibot/templates
```

---

## 리스크 관리 정책

### 핵심 규칙

1. **잔고 초과 금지**
   - 봇 합계가 총 잔고 초과 불가
   - 코드 레벨에서 강제
   ```python
   if used_amount + amount > total_balance:
       return (False, "잔고가 부족합니다")
   ```

2. **심볼 중복 금지**
   - 동일 심볼에 2개 이상 봇 불가
   - 포지션 충돌 방지

3. **최대 봇 개수**
   - 사용자당 5개 제한
   - 서버 리소스 보호

### 에러 처리

```python
# 잔고 부족
raise HTTPException(400, "잔고가 부족합니다")

# 중복 봇
raise HTTPException(400, "이미 실행 중인 봇")

# 최대 개수 초과
raise HTTPException(400, "최대 5개의 봇만 운용할 수 있습니다")

# 거래소 에러
bot.status = "error"
bot.error_message = str(e)
```

---

## 작업 체크리스트

> **주의**: v2에서는 레거시 호환성 유지 제거, 단순화됨

### Phase 1: 데이터베이스 (Day 1)

- [ ] **1.1** `BotInstance` 모델에 새 필드 추가
- [ ] **1.2** Alembic 마이그레이션 파일 생성
- [ ] **1.3** 로컬에서 마이그레이션 테스트

### Phase 2: 백엔드 API (Day 1-2)

- [ ] **2.1** Pydantic 스키마 작성: `multibot_schema.py`
- [ ] **2.2** `BalanceController` 서비스 구현
- [ ] **2.3** `MultiBotManager` 서비스 구현
- [ ] **2.4** API 라우터 작성: `multibot.py`
- [ ] **2.5** `main.py`에 라우터 등록
- [ ] **2.6** API 엔드포인트 테스트 (curl/Postman)
- [ ] **2.7** 유닛 테스트 작성

### Phase 3: 봇 러너 수정 (Day 2-3)

- [ ] **3.1** `BotRunner` 멀티 인스턴스 구조로 리팩토링
- [ ] **3.2** `start_instance()`, `stop_instance()` 메서드 구현
- [ ] **3.3** 인스턴스별 독립 루프 구현
- [ ] **3.4** `SharedWebSocketManager` 구현
- [ ] **3.5** 포지션 청산 로직 (봇 중지 시)
- [ ] **3.6** 에러 핸들링 및 복구 로직
- [ ] **3.7** 서버 재시작 시 봇 복구 로직

### Phase 4: 프론트엔드 (Day 3-4)

- [ ] **4.1** TypeScript 타입 정의: `multibot.ts`
- [ ] **4.2** API 훅 작성: `useMultiBot.ts`
- [ ] **4.3** `StrategyCard` 컴포넌트
- [ ] **4.4** `StrategyCardList` 컴포넌트
- [ ] **4.5** `BotStatusCard` 컴포넌트
- [ ] **4.6** `ActiveBotsList` 컴포넌트
- [ ] **4.7** `BalanceSummary` 컴포넌트
- [ ] **4.8** `BotStartModal` 컴포넌트
- [ ] **4.9** `BotDetailModal` 컴포넌트
- [ ] **4.10** `MultiBotPage` 페이지
- [ ] **4.11** 라우팅 설정
- [ ] **4.12** 네비게이션 메뉴 추가

### Phase 5: 테스트 및 배포 (Day 5)

- [ ] **5.1** 잔고 검증 테스트
- [ ] **5.2** 봇 시작/중지 테스트
- [ ] **5.3** 동시 다중 봇 테스트
- [ ] **5.4** UI/UX 테스트
- [ ] **5.5** Production 마이그레이션
- [ ] **5.6** Production 배포
- [ ] **5.7** 헬스 체크 및 모니터링
- [ ] **5.8** 문서 업데이트

---

## 작업 협업 지침

### AI 간 작업 분배

```
AI-1: Phase 1 (DB) + Phase 2.1-2.3 (스키마, 서비스)
AI-2: Phase 2.4-2.7 (API) + Phase 3.1-3.4 (봇러너)
AI-3: Phase 3.5-3.7 (봇러너) + Phase 4.1-4.6 (프론트)
AI-4: Phase 4.7-4.12 (프론트) + Phase 5 (테스트/배포)
```

### 커밋 컨벤션

```
feat(multibot): Add BotInstance columns          # Phase 1.1
feat(multibot): Implement BalanceController      # Phase 2.2
refactor(bot): Support multi-instance running    # Phase 3.1
feat(frontend): Add StrategyCard component       # Phase 4.3
test(multibot): Add balance validation tests     # Phase 5.1
```

### 충돌 방지

1. 작업 전 `git pull` 필수
2. 한 파일을 여러 AI가 동시 수정 금지
3. 체크리스트 업데이트 후 커밋

---

**문서 끝**
