# 작업 지시서 B: 백테스트 시스템 구현

## 📌 담당 영역
- 과거 캔들 데이터 수집
- 그리드 트레이딩 시뮬레이션 엔진
- 수익률/낙폭 계산 알고리즘
- 백테스트 API 연동

---

## 1. 사전 요구사항

### 1.1 의존성
```bash
# Task A의 DB 모델이 완료되어야 함
# GridBotTemplate 테이블이 존재해야 함
```

### 1.2 필요 파일 위치
```
backend/
├── src/
│   ├── services/
│   │   ├── grid_backtester.py       # 새로 생성 (메인 백테스터)
│   │   └── candle_data_service.py   # 새로 생성 (캔들 데이터 수집)
│   ├── schemas/
│   │   └── backtest_schema.py       # 새로 생성
│   └── api/
│       └── admin_grid_template.py   # 수정 (백테스트 API 연동)
```

---

## 2. 작업 1: 캔들 데이터 수집 서비스

### 2.1 파일: `backend/src/services/candle_data_service.py` (새로 생성)

```python
"""
Candle Data Service
- Bitget API에서 과거 캔들 데이터 수집
- 캐싱을 통한 효율적인 데이터 관리
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from decimal import Decimal
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Candle:
    """캔들 데이터 구조체"""
    timestamp: int          # Unix timestamp (ms)
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp / 1000)


class CandleDataService:
    """
    캔들 데이터 수집 서비스

    Bitget API 사용:
    - 선물: https://api.bitget.com/api/v2/mix/market/candles
    - 최대 1000개 캔들/요청
    """

    BITGET_FUTURES_CANDLE_URL = "https://api.bitget.com/api/v2/mix/market/candles"

    # 캔들 간격 (분)
    GRANULARITY_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1H": "1H",
        "4H": "4H",
        "1D": "1D"
    }

    def __init__(self):
        self._cache: Dict[str, List[Candle]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)  # 캐시 유효시간

    async def get_candles(
        self,
        symbol: str,
        granularity: str = "5m",
        days: int = 30,
        product_type: str = "USDT-FUTURES"
    ) -> List[Candle]:
        """
        과거 캔들 데이터 조회

        Args:
            symbol: 심볼 (예: "SOLUSDT")
            granularity: 캔들 간격 ("1m", "5m", "15m", "30m", "1H", "4H", "1D")
            days: 조회 기간 (일)
            product_type: 상품 유형 ("USDT-FUTURES", "COIN-FUTURES")

        Returns:
            List[Candle]: 캔들 데이터 리스트 (오래된 순)
        """
        cache_key = f"{symbol}_{granularity}_{days}"

        # 캐시 확인
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached candle data for {cache_key}")
            return self._cache[cache_key]

        # API에서 데이터 수집
        candles = await self._fetch_candles(
            symbol=symbol,
            granularity=granularity,
            days=days,
            product_type=product_type
        )

        # 캐시 저장
        self._cache[cache_key] = candles
        self._cache_expiry[cache_key] = datetime.now() + self._cache_ttl

        return candles

    async def _fetch_candles(
        self,
        symbol: str,
        granularity: str,
        days: int,
        product_type: str
    ) -> List[Candle]:
        """Bitget API에서 캔들 데이터 가져오기"""

        # 시간 계산
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        # 캔들 간격에 따른 예상 개수 계산
        minutes_per_candle = self._get_minutes(granularity)
        total_minutes = days * 24 * 60
        expected_candles = total_minutes // minutes_per_candle

        logger.info(
            f"Fetching {expected_candles} candles for {symbol} "
            f"({granularity}, {days} days)"
        )

        all_candles = []
        current_end = end_time

        async with aiohttp.ClientSession() as session:
            while current_end > start_time:
                params = {
                    "symbol": symbol,
                    "productType": product_type,
                    "granularity": granularity,
                    "endTime": str(current_end),
                    "limit": "1000"  # 최대 1000개
                }

                try:
                    async with session.get(
                        self.BITGET_FUTURES_CANDLE_URL,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            logger.error(f"API error: {response.status}")
                            break

                        data = await response.json()

                        if data.get("code") != "00000":
                            logger.error(f"API error: {data.get('msg')}")
                            break

                        candle_data = data.get("data", [])
                        if not candle_data:
                            break

                        # 캔들 파싱
                        for c in candle_data:
                            candle = Candle(
                                timestamp=int(c[0]),
                                open=Decimal(c[1]),
                                high=Decimal(c[2]),
                                low=Decimal(c[3]),
                                close=Decimal(c[4]),
                                volume=Decimal(c[5])
                            )
                            all_candles.append(candle)

                        # 다음 배치를 위한 시간 업데이트
                        oldest_timestamp = min(int(c[0]) for c in candle_data)
                        current_end = oldest_timestamp - 1

                        # API 레이트 리밋 방지
                        await asyncio.sleep(0.1)

                except asyncio.TimeoutError:
                    logger.error("API timeout")
                    break
                except Exception as e:
                    logger.error(f"Error fetching candles: {e}")
                    break

        # 시간순 정렬 (오래된 것이 앞에)
        all_candles.sort(key=lambda c: c.timestamp)

        # start_time 이후의 캔들만 필터링
        filtered = [c for c in all_candles if c.timestamp >= start_time]

        logger.info(f"Fetched {len(filtered)} candles for {symbol}")
        return filtered

    def _get_minutes(self, granularity: str) -> int:
        """캔들 간격을 분으로 변환"""
        mapping = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1H": 60,
            "4H": 240,
            "1D": 1440
        }
        return mapping.get(granularity, 5)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 확인"""
        if cache_key not in self._cache:
            return False
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        self._cache_expiry.clear()
```

### 2.2 검증 체크리스트
- [ ] candle_data_service.py 파일 생성됨
- [ ] Bitget API 호출 성공
- [ ] 캐싱 동작 확인
- [ ] 캔들 데이터 시간순 정렬됨

---

## 3. 작업 2: 그리드 백테스터 엔진

### 3.1 파일: `backend/src/services/grid_backtester.py` (새로 생성)

```python
"""
Grid Bot Backtester
- 과거 데이터로 그리드 트레이딩 시뮬레이션
- 수익률, 낙폭, 승률 등 계산
"""
from decimal import Decimal, ROUND_DOWN
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from src.services.candle_data_service import CandleDataService, Candle
from src.database.models import GridMode, PositionDirection

logger = logging.getLogger(__name__)


@dataclass
class GridLevel:
    """그리드 레벨 상태"""
    index: int
    price: Decimal
    is_filled: bool = False
    fill_price: Optional[Decimal] = None
    fill_time: Optional[datetime] = None


@dataclass
class SimulatedTrade:
    """시뮬레이션된 거래"""
    buy_price: Decimal
    sell_price: Decimal
    quantity: Decimal
    profit: Decimal
    profit_pct: Decimal
    buy_time: datetime
    sell_time: datetime
    grid_index: int


@dataclass
class BacktestResult:
    """백테스트 결과"""
    # 수익률
    total_roi: Decimal              # 총 수익률 (%)
    roi_30d: Decimal                # 30일 환산 ROI (%)

    # 위험 지표
    max_drawdown: Decimal           # 최대 낙폭 (%)
    sharpe_ratio: Optional[Decimal] = None  # 샤프 비율

    # 거래 통계
    total_trades: int = 0           # 총 거래 수
    winning_trades: int = 0         # 이긴 거래 수
    losing_trades: int = 0          # 진 거래 수
    win_rate: Decimal = Decimal('0')  # 승률 (%)

    # 수익 통계
    total_profit: Decimal = Decimal('0')        # 총 수익 (USDT)
    avg_profit_per_trade: Decimal = Decimal('0')  # 거래당 평균 수익
    max_profit_trade: Decimal = Decimal('0')    # 최대 수익 거래
    max_loss_trade: Decimal = Decimal('0')      # 최대 손실 거래

    # 시계열 데이터
    daily_roi: List[float] = field(default_factory=list)  # 일별 ROI (차트용)
    equity_curve: List[float] = field(default_factory=list)  # 자산 곡선

    # 메타 정보
    backtest_days: int = 30
    total_candles: int = 0
    grid_cycles_completed: int = 0

    def to_dict(self) -> dict:
        return {
            "total_roi": float(self.total_roi),
            "roi_30d": float(self.roi_30d),
            "max_drawdown": float(self.max_drawdown),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": float(self.win_rate),
            "total_profit": float(self.total_profit),
            "avg_profit_per_trade": float(self.avg_profit_per_trade),
            "daily_roi": self.daily_roi,
            "backtest_days": self.backtest_days,
            "grid_cycles_completed": self.grid_cycles_completed
        }


class GridBacktester:
    """
    그리드봇 백테스터

    시뮬레이션 로직:
    1. 그리드 가격 배열 계산
    2. 각 캔들마다 가격이 그리드를 통과하는지 확인
    3. 통과 시 매수/매도 시뮬레이션
    4. 수수료 차감
    5. 일별 수익률 계산
    """

    # 수수료율 (Bitget 기준)
    MAKER_FEE = Decimal('0.0002')  # 0.02%
    TAKER_FEE = Decimal('0.0006')  # 0.06%

    def __init__(self):
        self.candle_service = CandleDataService()

    async def run_backtest(
        self,
        symbol: str,
        direction: PositionDirection,
        lower_price: Decimal,
        upper_price: Decimal,
        grid_count: int,
        grid_mode: GridMode,
        leverage: int,
        investment: Decimal,
        days: int = 30,
        granularity: str = "5m"
    ) -> BacktestResult:
        """
        백테스트 실행

        Args:
            symbol: 심볼 (예: "SOLUSDT")
            direction: 포지션 방향 (LONG/SHORT)
            lower_price: 하단 가격
            upper_price: 상단 가격
            grid_count: 그리드 개수
            grid_mode: 그리드 모드 (ARITHMETIC/GEOMETRIC)
            leverage: 레버리지
            investment: 총 투자금액 (USDT)
            days: 백테스트 기간 (일)
            granularity: 캔들 간격

        Returns:
            BacktestResult: 백테스트 결과
        """
        logger.info(
            f"Starting backtest: {symbol} {direction.value} "
            f"[{lower_price}-{upper_price}] x{leverage} {grid_count} grids"
        )

        # 1. 캔들 데이터 수집
        candles = await self.candle_service.get_candles(
            symbol=symbol,
            granularity=granularity,
            days=days
        )

        if not candles:
            raise ValueError(f"No candle data available for {symbol}")

        # 2. 그리드 가격 계산
        grid_prices = self._calculate_grid_prices(
            lower_price, upper_price, grid_count, grid_mode
        )

        # 3. 그리드당 투자금액 계산
        per_grid_amount = (investment * leverage) / grid_count

        # 4. 시뮬레이션 실행
        result = self._simulate(
            candles=candles,
            grid_prices=grid_prices,
            direction=direction,
            per_grid_amount=per_grid_amount,
            leverage=leverage,
            investment=investment
        )

        result.backtest_days = days
        result.total_candles = len(candles)

        logger.info(
            f"Backtest complete: ROI={result.roi_30d}%, "
            f"MDD={result.max_drawdown}%, Trades={result.total_trades}"
        )

        return result

    def _simulate(
        self,
        candles: List[Candle],
        grid_prices: List[Decimal],
        direction: PositionDirection,
        per_grid_amount: Decimal,
        leverage: int,
        investment: Decimal
    ) -> BacktestResult:
        """시뮬레이션 실행"""

        # 상태 초기화
        grids: List[GridLevel] = [
            GridLevel(index=i, price=p)
            for i, p in enumerate(grid_prices)
        ]

        trades: List[SimulatedTrade] = []
        equity = investment  # 현재 자산
        peak_equity = investment  # 최고 자산
        max_drawdown = Decimal('0')

        daily_equity: Dict[str, Decimal] = {}
        current_date = None

        # 첫 캔들 가격 기준으로 초기 그리드 설정
        initial_price = candles[0].close

        # LONG: 현재가 아래 그리드에 매수, SHORT: 현재가 위 그리드에 매도
        for grid in grids:
            if direction == PositionDirection.LONG:
                if grid.price < initial_price:
                    grid.is_filled = True
                    grid.fill_price = grid.price
                    grid.fill_time = candles[0].datetime
            else:  # SHORT
                if grid.price > initial_price:
                    grid.is_filled = True
                    grid.fill_price = grid.price
                    grid.fill_time = candles[0].datetime

        # 각 캔들 순회
        for candle in candles:
            # 일별 자산 기록
            date_str = candle.datetime.strftime("%Y-%m-%d")
            if date_str != current_date:
                current_date = date_str
                daily_equity[date_str] = equity

            # 가격 범위 (고가-저가)
            price_high = candle.high
            price_low = candle.low

            # 그리드 통과 확인 및 거래 실행
            for i, grid in enumerate(grids):
                if direction == PositionDirection.LONG:
                    trades_executed = self._process_long_grid(
                        grid=grid,
                        grids=grids,
                        price_low=price_low,
                        price_high=price_high,
                        per_grid_amount=per_grid_amount,
                        candle=candle,
                        trades=trades
                    )
                else:
                    trades_executed = self._process_short_grid(
                        grid=grid,
                        grids=grids,
                        price_low=price_low,
                        price_high=price_high,
                        per_grid_amount=per_grid_amount,
                        candle=candle,
                        trades=trades
                    )

                # 거래 수익 반영
                for trade in trades_executed:
                    equity += trade.profit

            # 최대 낙폭 계산
            if equity > peak_equity:
                peak_equity = equity
            drawdown = ((peak_equity - equity) / peak_equity * 100) if peak_equity > 0 else Decimal('0')
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # 결과 계산
        total_profit = sum(t.profit for t in trades)
        total_roi = (total_profit / investment * 100) if investment > 0 else Decimal('0')

        # 일별 ROI 계산
        daily_roi = []
        prev_equity = investment
        for date_str in sorted(daily_equity.keys()):
            day_equity = daily_equity[date_str]
            day_roi = ((day_equity - prev_equity) / prev_equity * 100) if prev_equity > 0 else 0
            daily_roi.append(float(day_roi))
            prev_equity = day_equity

        # 누적 ROI로 변환 (차트용)
        cumulative_roi = []
        cum = 0
        for roi in daily_roi:
            cum += roi
            cumulative_roi.append(round(cum, 2))

        winning = [t for t in trades if t.profit > 0]
        losing = [t for t in trades if t.profit <= 0]

        return BacktestResult(
            total_roi=total_roi.quantize(Decimal('0.01')),
            roi_30d=total_roi.quantize(Decimal('0.01')),  # 이미 30일 기준
            max_drawdown=max_drawdown.quantize(Decimal('0.01')),
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=(Decimal(len(winning)) / len(trades) * 100).quantize(Decimal('0.01')) if trades else Decimal('0'),
            total_profit=total_profit.quantize(Decimal('0.01')),
            avg_profit_per_trade=(total_profit / len(trades)).quantize(Decimal('0.01')) if trades else Decimal('0'),
            max_profit_trade=max((t.profit for t in trades), default=Decimal('0')),
            max_loss_trade=min((t.profit for t in trades), default=Decimal('0')),
            daily_roi=cumulative_roi,
            equity_curve=[float(daily_equity.get(d, investment)) for d in sorted(daily_equity.keys())],
            grid_cycles_completed=len(trades)
        )

    def _process_long_grid(
        self,
        grid: GridLevel,
        grids: List[GridLevel],
        price_low: Decimal,
        price_high: Decimal,
        per_grid_amount: Decimal,
        candle: Candle,
        trades: List[SimulatedTrade]
    ) -> List[SimulatedTrade]:
        """
        LONG 그리드 처리

        - 가격 하락 시 매수 (grid price에서)
        - 가격 상승 시 매도 (다음 grid price에서)
        """
        new_trades = []

        # 매수: 가격이 그리드 아래로 내려갔다가 올라올 때
        if not grid.is_filled and price_low <= grid.price:
            grid.is_filled = True
            grid.fill_price = grid.price
            grid.fill_time = candle.datetime

        # 매도: 채워진 그리드에서 가격이 다음 그리드까지 올라갈 때
        if grid.is_filled and grid.index < len(grids) - 1:
            next_grid = grids[grid.index + 1]
            if price_high >= next_grid.price:
                # 거래 기록
                quantity = per_grid_amount / grid.fill_price
                sell_price = next_grid.price

                # 수수료 계산
                buy_fee = grid.fill_price * quantity * self.TAKER_FEE
                sell_fee = sell_price * quantity * self.TAKER_FEE
                total_fee = buy_fee + sell_fee

                gross_profit = (sell_price - grid.fill_price) * quantity
                net_profit = gross_profit - total_fee

                trade = SimulatedTrade(
                    buy_price=grid.fill_price,
                    sell_price=sell_price,
                    quantity=quantity,
                    profit=net_profit,
                    profit_pct=((sell_price - grid.fill_price) / grid.fill_price * 100),
                    buy_time=grid.fill_time,
                    sell_time=candle.datetime,
                    grid_index=grid.index
                )
                new_trades.append(trade)
                trades.append(trade)

                # 그리드 리셋 (다음 사이클 준비)
                grid.is_filled = False
                grid.fill_price = None
                grid.fill_time = None

        return new_trades

    def _process_short_grid(
        self,
        grid: GridLevel,
        grids: List[GridLevel],
        price_low: Decimal,
        price_high: Decimal,
        per_grid_amount: Decimal,
        candle: Candle,
        trades: List[SimulatedTrade]
    ) -> List[SimulatedTrade]:
        """
        SHORT 그리드 처리

        - 가격 상승 시 매도 (grid price에서)
        - 가격 하락 시 매수 (다음 grid price에서)
        """
        new_trades = []

        # 매도 진입: 가격이 그리드 위로 올라갔을 때
        if not grid.is_filled and price_high >= grid.price:
            grid.is_filled = True
            grid.fill_price = grid.price
            grid.fill_time = candle.datetime

        # 매수 청산: 채워진 그리드에서 가격이 아래 그리드까지 내려갈 때
        if grid.is_filled and grid.index > 0:
            prev_grid = grids[grid.index - 1]
            if price_low <= prev_grid.price:
                # 거래 기록 (숏 포지션)
                quantity = per_grid_amount / grid.fill_price
                buy_price = prev_grid.price  # 청산 가격

                # 수수료 계산
                sell_fee = grid.fill_price * quantity * self.TAKER_FEE
                buy_fee = buy_price * quantity * self.TAKER_FEE
                total_fee = sell_fee + buy_fee

                # 숏이므로 매도가 - 매수가 = 수익
                gross_profit = (grid.fill_price - buy_price) * quantity
                net_profit = gross_profit - total_fee

                trade = SimulatedTrade(
                    buy_price=buy_price,  # 청산가
                    sell_price=grid.fill_price,  # 진입가
                    quantity=quantity,
                    profit=net_profit,
                    profit_pct=((grid.fill_price - buy_price) / grid.fill_price * 100),
                    buy_time=candle.datetime,  # 청산 시간
                    sell_time=grid.fill_time,  # 진입 시간
                    grid_index=grid.index
                )
                new_trades.append(trade)
                trades.append(trade)

                # 그리드 리셋
                grid.is_filled = False
                grid.fill_price = None
                grid.fill_time = None

        return new_trades

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
            # 등차 방식: 동일 가격 간격
            step = (upper_price - lower_price) / (grid_count - 1)
            for i in range(grid_count):
                price = lower_price + (step * i)
                prices.append(price.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))
        else:
            # 등비 방식: 동일 퍼센트 간격
            import math
            ratio = math.pow(float(upper_price / lower_price), 1 / (grid_count - 1))
            for i in range(grid_count):
                price = lower_price * Decimal(str(pow(ratio, i)))
                prices.append(price.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))

        return prices


# 싱글톤 인스턴스
_backtester_instance: Optional[GridBacktester] = None


def get_grid_backtester() -> GridBacktester:
    """GridBacktester 싱글톤 인스턴스 반환"""
    global _backtester_instance
    if _backtester_instance is None:
        _backtester_instance = GridBacktester()
    return _backtester_instance
```

### 3.2 검증 체크리스트
- [ ] grid_backtester.py 파일 생성됨
- [ ] LONG 그리드 로직 정상 동작
- [ ] SHORT 그리드 로직 정상 동작
- [ ] 수수료 계산 정확
- [ ] 일별 ROI 계산 정확

---

## 4. 작업 3: 백테스트 스키마

### 4.1 파일: `backend/src/schemas/backtest_schema.py` (새로 생성)

```python
"""
Backtest Schemas
"""
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

from src.database.models import GridMode, PositionDirection


class BacktestRequest(BaseModel):
    """백테스트 요청 (관리자용 직접 테스트)"""
    symbol: str = Field(..., min_length=3, max_length=20)
    direction: PositionDirection
    lower_price: Decimal = Field(..., gt=0)
    upper_price: Decimal = Field(..., gt=0)
    grid_count: int = Field(..., ge=2, le=200)
    grid_mode: GridMode = GridMode.ARITHMETIC
    leverage: int = Field(default=5, ge=1, le=125)
    investment: Decimal = Field(default=Decimal('1000'), gt=0)
    days: int = Field(default=30, ge=7, le=90)
    granularity: str = Field(default="5m")


class BacktestResponse(BaseModel):
    """백테스트 응답"""
    success: bool = True

    # 주요 지표
    roi_30d: float              # 30일 ROI (%)
    max_drawdown: float         # 최대 낙폭 (%)
    total_trades: int           # 총 거래 수
    win_rate: float             # 승률 (%)

    # 수익 정보
    total_profit: float         # 총 수익 (USDT)
    avg_profit_per_trade: float # 거래당 평균 수익

    # 차트 데이터
    daily_roi: List[float]      # 일별 누적 ROI (30개)

    # 메타 정보
    backtest_days: int
    total_candles: int
    grid_cycles_completed: int


class BacktestSummary(BaseModel):
    """간단한 백테스트 결과 요약"""
    roi_30d: float
    max_drawdown: float
    win_rate: float
    total_trades: int
```

---

## 5. 작업 4: 관리자 API 연동

### 5.1 파일 수정: `backend/src/api/admin_grid_template.py`

기존 파일에서 `run_backtest` 엔드포인트를 업데이트:

```python
# 기존 import에 추가
from src.services.grid_backtester import get_grid_backtester
from src.schemas.backtest_schema import BacktestRequest, BacktestResponse


@router.post("/{template_id}/backtest", response_model=BacktestResponse)
async def run_backtest(
    template_id: int,
    days: int = Query(30, ge=7, le=90, description="Backtest period in days"),
    granularity: str = Query("5m", description="Candle granularity"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    템플릿 백테스트 실행 (관리자)

    - 과거 데이터로 그리드 시뮬레이션
    - 결과를 템플릿에 자동 저장
    """
    service = GridTemplateService(db)
    template = await service.get_template_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 백테스트 실행
    backtester = get_grid_backtester()

    try:
        result = await backtester.run_backtest(
            symbol=template.symbol,
            direction=template.direction,
            lower_price=template.lower_price,
            upper_price=template.upper_price,
            grid_count=template.grid_count,
            grid_mode=template.grid_mode,
            leverage=template.leverage,
            investment=template.min_investment,  # 최소 투자금액 기준
            days=days,
            granularity=granularity
        )

        # 결과를 템플릿에 저장
        await service.save_backtest_result(
            template_id=template_id,
            roi_30d=result.roi_30d,
            max_drawdown=result.max_drawdown,
            total_trades=result.total_trades,
            win_rate=result.win_rate,
            roi_history=result.daily_roi
        )

        return BacktestResponse(
            success=True,
            roi_30d=float(result.roi_30d),
            max_drawdown=float(result.max_drawdown),
            total_trades=result.total_trades,
            win_rate=float(result.win_rate),
            total_profit=float(result.total_profit),
            avg_profit_per_trade=float(result.avg_profit_per_trade),
            daily_roi=result.daily_roi,
            backtest_days=result.backtest_days,
            total_candles=result.total_candles,
            grid_cycles_completed=result.grid_cycles_completed
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Backtest failed")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.post("/backtest/preview", response_model=BacktestResponse)
async def preview_backtest(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    백테스트 미리보기 (템플릿 저장 전 테스트)

    - 템플릿 생성 전에 설정값 검증용
    - 결과 저장 안함
    """
    backtester = get_grid_backtester()

    try:
        result = await backtester.run_backtest(
            symbol=request.symbol,
            direction=request.direction,
            lower_price=request.lower_price,
            upper_price=request.upper_price,
            grid_count=request.grid_count,
            grid_mode=request.grid_mode,
            leverage=request.leverage,
            investment=request.investment,
            days=request.days,
            granularity=request.granularity
        )

        return BacktestResponse(
            success=True,
            roi_30d=float(result.roi_30d),
            max_drawdown=float(result.max_drawdown),
            total_trades=result.total_trades,
            win_rate=float(result.win_rate),
            total_profit=float(result.total_profit),
            avg_profit_per_trade=float(result.avg_profit_per_trade),
            daily_roi=result.daily_roi,
            backtest_days=result.backtest_days,
            total_candles=result.total_candles,
            grid_cycles_completed=result.grid_cycles_completed
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Backtest preview failed")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")
```

---

## 6. 테스트 방법

### 6.1 단위 테스트

```python
# tests/test_grid_backtester.py
import pytest
from decimal import Decimal
from src.services.grid_backtester import GridBacktester
from src.database.models import GridMode, PositionDirection


@pytest.mark.asyncio
async def test_backtest_long():
    """LONG 그리드 백테스트 테스트"""
    backtester = GridBacktester()

    result = await backtester.run_backtest(
        symbol="SOLUSDT",
        direction=PositionDirection.LONG,
        lower_price=Decimal("120"),
        upper_price=Decimal("150"),
        grid_count=30,
        grid_mode=GridMode.ARITHMETIC,
        leverage=5,
        investment=Decimal("500"),
        days=7  # 짧은 테스트
    )

    assert result.total_trades >= 0
    assert result.roi_30d is not None
    assert result.max_drawdown >= 0
    assert len(result.daily_roi) > 0


@pytest.mark.asyncio
async def test_backtest_short():
    """SHORT 그리드 백테스트 테스트"""
    backtester = GridBacktester()

    result = await backtester.run_backtest(
        symbol="BTCUSDT",
        direction=PositionDirection.SHORT,
        lower_price=Decimal("95000"),
        upper_price=Decimal("105000"),
        grid_count=20,
        grid_mode=GridMode.ARITHMETIC,
        leverage=10,
        investment=Decimal("1000"),
        days=7
    )

    assert result.total_trades >= 0
    assert result.roi_30d is not None
```

### 6.2 API 테스트

```bash
# 1. 토큰 획득
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"admin"}' | jq -r '.access_token')

# 2. 백테스트 미리보기
curl -X POST http://localhost:8000/admin/grid-templates/backtest/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SOLUSDT",
    "direction": "short",
    "lower_price": "120",
    "upper_price": "150",
    "grid_count": 30,
    "grid_mode": "ARITHMETIC",
    "leverage": 5,
    "investment": "500",
    "days": 30
  }'

# 3. 템플릿 백테스트 실행 (template_id=1)
curl -X POST "http://localhost:8000/admin/grid-templates/1/backtest?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. 성능 고려사항

### 7.1 캔들 데이터 최적화
- 30일 5분봉 = 약 8,640개 캔들
- 메모리: 캔들당 ~100바이트 = ~860KB
- 캐시 TTL 1시간으로 중복 API 호출 방지

### 7.2 백테스트 최적화
- 그리드 100개, 캔들 8,640개 = 864,000 반복
- 각 반복 O(1) 연산으로 총 O(n*m)
- 예상 실행 시간: 1-3초

### 7.3 동시성 처리
- 백테스트는 CPU 바운드 작업
- 여러 템플릿 동시 백테스트 시 asyncio.gather() 활용
- 또는 백그라운드 작업 큐 (Celery) 도입 고려

---

## 8. 완료 체크리스트

### Phase B 완료 조건
- [ ] CandleDataService 구현 완료
- [ ] GridBacktester 구현 완료
- [ ] LONG/SHORT 시뮬레이션 정확
- [ ] 수수료 계산 정확
- [ ] 일별 ROI 계산 정확
- [ ] 백테스트 API 연동 완료
- [ ] 백테스트 미리보기 API 동작
- [ ] 단위 테스트 통과
- [ ] API 테스트 통과

---

## 9. 다음 단계

- **Task C (프론트엔드)**: ROI 차트, 템플릿 카드 구현
- **Task D (관리자 페이지)**: 백테스트 실행 UI
