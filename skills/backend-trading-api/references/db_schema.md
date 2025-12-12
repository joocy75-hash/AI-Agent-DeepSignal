# 데이터베이스 스키마 참조

## ERD 개요

```
users (1) ──┬── (N) api_keys
            ├── (N) strategies
            ├── (N) trades
            ├── (N) positions
            ├── (N) equities
            ├── (1) bot_status
            ├── (1) bot_config
            ├── (1) risk_settings
            ├── (1) user_settings
            └── (N) trading_signals

strategies (1) ── (N) trades
backtest_results (1) ── (N) backtest_trades
```

---

## 모델 정의

### User (사용자)

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # 소셜 로그인은 None
    name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String, default="user")  # 'user' or 'admin'
    exchange = Column(String, default="bitget")
    is_active = Column(Boolean, default=True)
    suspended_at = Column(DateTime, nullable=True)

    # OAuth
    oauth_provider = Column(String(20), nullable=True)  # 'google', 'kakao'
    oauth_id = Column(String(255), nullable=True, index=True)
    profile_image = Column(String(500), nullable=True)

    # 2FA
    totp_secret = Column(String, nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
```

### ApiKey (API 키)

```python
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    encrypted_api_key = Column(Text, nullable=False)     # Fernet 암호화
    encrypted_secret_key = Column(Text, nullable=False)  # Fernet 암호화
    encrypted_passphrase = Column(Text, nullable=True)   # Fernet 암호화
```

### Strategy (전략)

```python
class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=True)    # 커스텀 전략 코드
    params = Column(Text, nullable=True)  # JSON 파라미터
    is_active = Column(Boolean, default=False)
```

### Trade (거래)

```python
class ExitReason(str, Enum):
    take_profit = "take_profit"
    stop_loss = "stop_loss"
    signal_reverse = "signal_reverse"
    manual = "manual"
    liquidation = "liquidation"


class Trade(Base):
    __tablename__ = "trades"

    __table_args__ = (
        Index("idx_trade_user_created", "user_id", "created_at"),
        Index("idx_trade_symbol", "symbol"),
        Index("idx_trade_strategy", "strategy_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # 'buy' or 'sell'
    qty = Column(Float, nullable=False)
    entry_price = Column(Numeric(18, 8), nullable=False)
    exit_price = Column(Numeric(18, 8), nullable=True)
    pnl = Column(Numeric(18, 8), default=0)
    pnl_percent = Column(Float, default=0)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    leverage = Column(Integer, default=1)
    exit_reason = Column(SQLEnum(ExitReason), default=ExitReason.manual)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Position (포지션)

```python
class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, nullable=False)
    entry_price = Column(Numeric(18, 8), nullable=False)
    size = Column(Float, nullable=False)
    side = Column(String, nullable=False)  # 'long' or 'short'
    pnl = Column(Numeric(18, 8), default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### BotStatus (봇 상태)

```python
class BotStatus(Base):
    __tablename__ = "bot_status"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    is_running = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### BotConfig (봇 설정)

```python
class BotConfig(Base):
    __tablename__ = "bot_config"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    max_risk_percent = Column(Float, default=1.0)
    leverage = Column(Integer, default=5)
    auto_tp = Column(Float, default=3.0)  # Take Profit %
    auto_sl = Column(Float, default=1.5)  # Stop Loss %
```

### RiskSettings (리스크 설정)

```python
class RiskSettings(Base):
    __tablename__ = "risk_settings"

    __table_args__ = (
        CheckConstraint("daily_loss_limit > 0", name="check_positive_loss_limit"),
        CheckConstraint("max_leverage >= 1 AND max_leverage <= 100", name="check_leverage_range"),
        CheckConstraint("max_positions >= 1 AND max_positions <= 50", name="check_positions_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    daily_loss_limit = Column(Float, nullable=False, default=500.0)  # USDT
    max_leverage = Column(Integer, nullable=False, default=10)
    max_positions = Column(Integer, nullable=False, default=5)
```

### BacktestResult (백테스트 결과)

```python
class BacktestResult(Base):
    __tablename__ = "backtest_results"

    __table_args__ = (
        Index("idx_backtest_user_created", "user_id", "created_at"),
        Index("idx_backtest_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pair = Column(String, nullable=True)
    timeframe = Column(String, nullable=True)
    initial_balance = Column(Float, nullable=False)
    final_balance = Column(Float, nullable=False)
    metrics = Column(Text, nullable=True)       # JSON
    equity_curve = Column(Text, nullable=True)  # JSON array
    params = Column(Text, nullable=True)        # JSON
    status = Column(String, default="queued")   # queued, running, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### TradingSignal (트레이딩 시그널)

```python
class TradingSignal(Base):
    __tablename__ = "trading_signals"

    __table_args__ = (
        Index("idx_signal_user_timestamp", "user_id", "timestamp"),
        Index("idx_signal_symbol", "symbol"),
        Index("idx_signal_strategy", "strategy_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    timeframe = Column(String(10), nullable=False)
    price = Column(Float, nullable=True)
    indicators = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)  # 0-1
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
```

---

## 쿼리 패턴

### 기본 조회

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 단일 조회
result = await session.execute(
    select(User).where(User.id == user_id)
)
user = result.scalars().first()

# 목록 조회 (페이지네이션)
result = await session.execute(
    select(Trade)
    .where(Trade.user_id == user_id)
    .order_by(Trade.created_at.desc())
    .offset(offset)
    .limit(limit)
)
trades = result.scalars().all()

# 조인 쿼리
result = await session.execute(
    select(Trade, Strategy)
    .join(Strategy, Trade.strategy_id == Strategy.id, isouter=True)
    .where(Trade.user_id == user_id)
)
```

### 집계 쿼리

```python
from sqlalchemy import func

# 총 거래 수
result = await session.execute(
    select(func.count(Trade.id))
    .where(Trade.user_id == user_id)
)
count = result.scalar()

# 총 손익
result = await session.execute(
    select(func.sum(Trade.pnl))
    .where(Trade.user_id == user_id)
)
total_pnl = result.scalar() or 0
```

### 생성/수정/삭제

```python
# 생성
new_item = MyModel(user_id=user_id, name="test")
session.add(new_item)
await session.commit()
await session.refresh(new_item)

# 수정
item.name = "updated"
await session.commit()

# 삭제
await session.delete(item)
await session.commit()
```

---

## 마이그레이션

### 새 마이그레이션 생성

```bash
# 모델 변경 감지하여 자동 생성
alembic revision --autogenerate -m "Add new_column to users"

# 수동 생성
alembic revision -m "Custom migration"
```

### 마이그레이션 적용

```bash
# 최신으로 업그레이드
alembic upgrade head

# 특정 버전으로
alembic upgrade abc123

# 롤백
alembic downgrade -1
```
