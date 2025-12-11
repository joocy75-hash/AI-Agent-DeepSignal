# 🗄️ 다중 봇 시스템 구현 계획서 (2/3)

# 📊 데이터베이스 상세 설계

---

## 📌 관련 문서

- 이전: `01_OVERVIEW.md`
- 다음: `03_IMPLEMENTATION_DETAIL.md`

---

## 🏗️ 테이블 설계

### 1. `bot_instances` - 봇 인스턴스 테이블

**목적**: 사용자별 여러 봇 인스턴스 관리

```sql
CREATE TABLE bot_instances (
    -- 기본 키
    id SERIAL PRIMARY KEY,
    
    -- 관계
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    
    -- 봇 정보
    name VARCHAR(100) NOT NULL,
    description TEXT,
    bot_type VARCHAR(20) NOT NULL DEFAULT 'ai_trend',
        -- 'ai_trend': AI 추세 추종 봇
        -- 'grid': 그리드 봇
    
    -- 잔고 할당
    allocation_percent DECIMAL(5,2) NOT NULL DEFAULT 10.0,
        -- 사용자 전체 잔고 중 이 봇에 할당된 비율 (%)
        -- 모든 봇의 합 <= 100%
    
    -- 심볼 설정
    symbol VARCHAR(20) NOT NULL DEFAULT 'BTCUSDT',
    
    -- 리스크 설정 (봇별로 다르게 설정 가능)
    max_leverage INTEGER NOT NULL DEFAULT 10 CHECK (max_leverage >= 1 AND max_leverage <= 100),
    max_positions INTEGER NOT NULL DEFAULT 3 CHECK (max_positions >= 1 AND max_positions <= 20),
    stop_loss_percent DECIMAL(5,2) DEFAULT 5.0,
    take_profit_percent DECIMAL(5,2) DEFAULT 10.0,
    
    -- 알림 설정
    telegram_notify BOOLEAN DEFAULT TRUE,
    
    -- 상태
    is_running BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,  -- soft delete용
    
    -- 실행 추적
    last_started_at TIMESTAMP,
    last_stopped_at TIMESTAMP,
    last_trade_at TIMESTAMP,
    last_error TEXT,
    
    -- 통계 (실시간 업데이트)
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 제약조건
    CONSTRAINT check_allocation CHECK (allocation_percent > 0 AND allocation_percent <= 100),
    CONSTRAINT unique_bot_name_per_user UNIQUE (user_id, name)
);

-- 인덱스
CREATE INDEX idx_bot_instances_user_id ON bot_instances(user_id);
CREATE INDEX idx_bot_instances_user_running ON bot_instances(user_id, is_running);
CREATE INDEX idx_bot_instances_type ON bot_instances(bot_type);
```

### 2. `grid_bot_configs` - 그리드 봇 설정 테이블

**목적**: 그리드 봇 전용 설정 저장

```sql
CREATE TABLE grid_bot_configs (
    -- 기본 키
    id SERIAL PRIMARY KEY,
    
    -- 관계 (1:1)
    bot_instance_id INTEGER NOT NULL UNIQUE REFERENCES bot_instances(id) ON DELETE CASCADE,
    
    -- 그리드 설정
    lower_price DECIMAL(20,8) NOT NULL,   -- 하한가 (예: $85,000)
    upper_price DECIMAL(20,8) NOT NULL,   -- 상한가 (예: $100,000)
    grid_count INTEGER NOT NULL DEFAULT 10 CHECK (grid_count >= 2 AND grid_count <= 100),
    grid_mode VARCHAR(20) DEFAULT 'arithmetic',
        -- 'arithmetic': 균등 간격
        -- 'geometric': 기하 간격 (% 기준)
    
    -- 투자 설정
    total_investment DECIMAL(20,8) NOT NULL,  -- 총 투자금 (USDT)
    per_grid_amount DECIMAL(20,8),            -- 그리드당 투자금 (자동 계산)
    
    -- 트리거 설정
    trigger_price DECIMAL(20,8),              -- 특정 가격에 시작 (선택)
    stop_upper DECIMAL(20,8),                 -- 상한 돌파 시 중지
    stop_lower DECIMAL(20,8),                 -- 하한 돌파 시 중지
    
    -- 상태 추적
    current_price DECIMAL(20,8),
    active_buy_orders INTEGER DEFAULT 0,
    active_sell_orders INTEGER DEFAULT 0,
    filled_buy_count INTEGER DEFAULT 0,
    filled_sell_count INTEGER DEFAULT 0,
    realized_profit DECIMAL(20,8) DEFAULT 0,
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 제약조건
    CONSTRAINT check_price_range CHECK (upper_price > lower_price),
    CONSTRAINT check_grid_count CHECK (grid_count >= 2)
);
```

### 3. `grid_orders` - 그리드 주문 테이블

**목적**: 각 그리드 라인의 주문 상태 추적

```sql
CREATE TABLE grid_orders (
    -- 기본 키
    id SERIAL PRIMARY KEY,
    
    -- 관계
    grid_config_id INTEGER NOT NULL REFERENCES grid_bot_configs(id) ON DELETE CASCADE,
    
    -- 그리드 정보
    grid_index INTEGER NOT NULL,              -- 0 ~ (grid_count-1)
    grid_price DECIMAL(20,8) NOT NULL,        -- 이 그리드의 가격
    
    -- 주문 상태
    buy_order_id VARCHAR(100),                -- Bitget 매수 주문 ID
    sell_order_id VARCHAR(100),               -- Bitget 매도 주문 ID
    status VARCHAR(20) DEFAULT 'pending',
        -- 'pending': 주문 대기
        -- 'buy_placed': 매수 주문 설정됨
        -- 'buy_filled': 매수 체결 (보유 중)
        -- 'sell_placed': 매도 주문 설정됨
        -- 'sell_filled': 매도 체결 (수익 실현)
    
    -- 체결 정보
    buy_filled_price DECIMAL(20,8),
    buy_filled_qty DECIMAL(20,8),
    buy_filled_at TIMESTAMP,
    sell_filled_price DECIMAL(20,8),
    sell_filled_qty DECIMAL(20,8),
    sell_filled_at TIMESTAMP,
    
    -- 수익
    profit DECIMAL(20,8) DEFAULT 0,
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 유니크 제약
    CONSTRAINT unique_grid_per_config UNIQUE (grid_config_id, grid_index)
);

-- 인덱스
CREATE INDEX idx_grid_orders_config ON grid_orders(grid_config_id);
CREATE INDEX idx_grid_orders_status ON grid_orders(status);
```

### 4. 기존 테이블 수정

#### `trades` 테이블 수정

```sql
-- 새 컬럼 추가
ALTER TABLE trades ADD COLUMN bot_instance_id INTEGER REFERENCES bot_instances(id);
ALTER TABLE trades ADD COLUMN trade_source VARCHAR(20) DEFAULT 'manual';
    -- 'manual': 수동 거래
    -- 'ai_bot': AI 봇 거래
    -- 'grid_bot': 그리드 봇 거래

-- 인덱스 추가
CREATE INDEX idx_trades_bot_instance ON trades(bot_instance_id);
```

---

## 🔗 테이블 관계 다이어그램

```
┌──────────────┐
│    users     │
│──────────────│
│ id (PK)      │
│ email        │
│ ...          │
└──────┬───────┘
       │
       │ 1:N
       ▼
┌──────────────────┐       1:1      ┌────────────────────┐
│  bot_instances   │───────────────▶│  grid_bot_configs  │
│──────────────────│                │────────────────────│
│ id (PK)          │                │ id (PK)            │
│ user_id (FK)     │                │ bot_instance_id    │
│ strategy_id (FK) │                │ lower_price        │
│ bot_type         │                │ upper_price        │
│ allocation_pct   │                │ grid_count         │
│ ...              │                │ ...                │
└────────┬─────────┘                └─────────┬──────────┘
         │                                    │
         │ 1:N                                │ 1:N
         ▼                                    ▼
┌──────────────────┐                ┌────────────────────┐
│     trades       │                │    grid_orders     │
│──────────────────│                │────────────────────│
│ id (PK)          │                │ id (PK)            │
│ bot_instance_id  │                │ grid_config_id(FK) │
│ ...              │                │ grid_index         │
└──────────────────┘                │ grid_price         │
                                    │ status             │
                                    └────────────────────┘
```

---

## 📝 SQLAlchemy 모델

### `database/models.py` 추가 내용

```python
class BotType(str, Enum):
    AI_TREND = "ai_trend"
    GRID = "grid"


class BotInstance(Base):
    __tablename__ = "bot_instances"
    
    __table_args__ = (
        CheckConstraint("allocation_percent > 0 AND allocation_percent <= 100"),
        UniqueConstraint("user_id", "name", name="unique_bot_name_per_user"),
        Index("idx_bot_instances_user_running", "user_id", "is_running"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="SET NULL"))
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    bot_type = Column(SQLEnum(BotType), default=BotType.AI_TREND, nullable=False)
    
    allocation_percent = Column(Numeric(5, 2), nullable=False, default=10.0)
    symbol = Column(String(20), nullable=False, default="BTCUSDT")
    
    max_leverage = Column(Integer, nullable=False, default=10)
    max_positions = Column(Integer, nullable=False, default=3)
    stop_loss_percent = Column(Numeric(5, 2), default=5.0)
    take_profit_percent = Column(Numeric(5, 2), default=10.0)
    
    telegram_notify = Column(Boolean, default=True)
    
    is_running = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    last_started_at = Column(DateTime)
    last_stopped_at = Column(DateTime)
    last_trade_at = Column(DateTime)
    last_error = Column(Text)
    
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Numeric(20, 8), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bot_instances")
    strategy = relationship("Strategy")
    grid_config = relationship("GridBotConfig", back_populates="bot_instance", uselist=False)
    trades = relationship("Trade", back_populates="bot_instance")


class GridMode(str, Enum):
    ARITHMETIC = "arithmetic"
    GEOMETRIC = "geometric"


class GridBotConfig(Base):
    __tablename__ = "grid_bot_configs"
    
    __table_args__ = (
        CheckConstraint("upper_price > lower_price"),
        CheckConstraint("grid_count >= 2 AND grid_count <= 100"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    bot_instance_id = Column(Integer, ForeignKey("bot_instances.id", ondelete="CASCADE"), 
                             nullable=False, unique=True)
    
    lower_price = Column(Numeric(20, 8), nullable=False)
    upper_price = Column(Numeric(20, 8), nullable=False)
    grid_count = Column(Integer, nullable=False, default=10)
    grid_mode = Column(SQLEnum(GridMode), default=GridMode.ARITHMETIC)
    
    total_investment = Column(Numeric(20, 8), nullable=False)
    per_grid_amount = Column(Numeric(20, 8))
    
    trigger_price = Column(Numeric(20, 8))
    stop_upper = Column(Numeric(20, 8))
    stop_lower = Column(Numeric(20, 8))
    
    current_price = Column(Numeric(20, 8))
    active_buy_orders = Column(Integer, default=0)
    active_sell_orders = Column(Integer, default=0)
    filled_buy_count = Column(Integer, default=0)
    filled_sell_count = Column(Integer, default=0)
    realized_profit = Column(Numeric(20, 8), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bot_instance = relationship("BotInstance", back_populates="grid_config")
    orders = relationship("GridOrder", back_populates="grid_config", cascade="all, delete-orphan")


class GridOrderStatus(str, Enum):
    PENDING = "pending"
    BUY_PLACED = "buy_placed"
    BUY_FILLED = "buy_filled"
    SELL_PLACED = "sell_placed"
    SELL_FILLED = "sell_filled"


class GridOrder(Base):
    __tablename__ = "grid_orders"
    
    __table_args__ = (
        UniqueConstraint("grid_config_id", "grid_index", name="unique_grid_per_config"),
        Index("idx_grid_orders_status", "status"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    grid_config_id = Column(Integer, ForeignKey("grid_bot_configs.id", ondelete="CASCADE"), nullable=False)
    
    grid_index = Column(Integer, nullable=False)
    grid_price = Column(Numeric(20, 8), nullable=False)
    
    buy_order_id = Column(String(100))
    sell_order_id = Column(String(100))
    status = Column(SQLEnum(GridOrderStatus), default=GridOrderStatus.PENDING)
    
    buy_filled_price = Column(Numeric(20, 8))
    buy_filled_qty = Column(Numeric(20, 8))
    buy_filled_at = Column(DateTime)
    sell_filled_price = Column(Numeric(20, 8))
    sell_filled_qty = Column(Numeric(20, 8))
    sell_filled_at = Column(DateTime)
    
    profit = Column(Numeric(20, 8), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grid_config = relationship("GridBotConfig", back_populates="orders")
```

---

## 🔄 마이그레이션 스크립트

### Alembic 마이그레이션

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "add_multi_bot_tables"

# 마이그레이션 실행
alembic upgrade head
```

---

**다음 문서**: `03_IMPLEMENTATION_DETAIL.md` (서비스 로직 상세 구현)
