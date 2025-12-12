# 📊 바이낸스 캔들 데이터 다운로드 마이그레이션 계획

> **작성일**: 2025-12-13
> **목적**: 백테스트용 캔들 데이터 소스를 Bitget → Binance로 변경
> **상태**: ✅ 구현 완료 (2025-12-13)
>
> **구현 완료 항목:**
>
> - ✅ `binance_rest.py` - Binance REST API 클라이언트
> - ✅ `candle_cache.py` - Binance/Bitget 선택 로직 추가
> - ✅ `download_binance_data.py` - 다운로드 스크립트
> - ✅ 통합 테스트 완료

---

## 📋 목차

1. [현재 상황 분석](#1-현재-상황-분석)
2. [마이그레이션 목표](#2-마이그레이션-목표)
3. [세부 작업 계획](#3-세부-작업-계획)
4. [구현 상세](#4-구현-상세)
5. [테스트 계획](#5-테스트-계획)
6. [롤백 전략](#6-롤백-전략)

---

## 1. 현재 상황 분석

### 1.1 현재 아키텍처

현재 백테스트 시스템은 **Bitget API**를 사용하여 캔들 데이터를 수집하고 있습니다.

```
[Data Flow]
Bitget API → bitget_rest.py → candle_cache.py → CSV 파일 저장
                                    ↓
                            candle_data_service.py
                                    ↓
                            grid_backtester.py
```

### 1.2 관련 파일 목록

| 파일 경로 | 역할 | 수정 필요 |
|-----------|------|-----------|
| `backend/src/services/bitget_rest.py` | Bitget REST API 클라이언트 | ❌ (유지) |
| `backend/src/services/candle_cache.py` | 캔들 캐시 매니저 | ⚠️ (확장) |
| `backend/src/services/candle_data_service.py` | 캔들 데이터 서비스 | ⚠️ (확장) |
| `backend/download_historical_data.py` | 다운로드 스크립트 | ⚠️ (확장) |
| `backend/candle_cache/` | 캐시 데이터 디렉토리 | ❌ (유지) |

### 1.3 현재 캐시 데이터 현황

```
backend/candle_cache/
├── BTCUSDT_1h.csv    (1,019개 캔들, ~42일)
├── BTCUSDT_4h.csv    (1,084개 캔들, ~6개월)
├── BTCUSDT_1d.csv    (1,441개 캔들, ~4년)
├── ETHUSDT_1h.csv    (1,019개 캔들)
├── ETHUSDT_4h.csv    (1,084개 캔들)
├── ETHUSDT_1m.csv    (44,091개 캔들, ~30일)
└── ... (총 10개 심볼)
```

**문제점:**

- Bitget API는 요청당 최대 1,000개 캔들 제한
- Rate Limit이 엄격함 (429 에러 빈발)
- 장기간 데이터 수집에 많은 시간 소요
- 일부 코인의 히스토리 데이터가 제한적

### 1.4 Bitget vs Binance 비교

| 항목 | Bitget | Binance |
|------|--------|---------|
| 요청당 최대 캔들 | 1,000개 | 1,500개 |
| Rate Limit | 20 req/sec | 1200 req/min |
| 히스토리 기간 | 2020년 5월~ | 2017년 7월~ |
| 선물 지원 | USDT-FUTURES | USDT-M Futures |
| 인증 필요 | 공개 API 가능 | 공개 API 가능 |

---

## 2. 마이그레이션 목표

### 2.1 핵심 목표

1. **더 많은 히스토리 데이터**: 2017년부터 현재까지 전체 데이터 수집
2. **더 빠른 수집 속도**: Binance의 관대한 Rate Limit 활용
3. **기존 시스템 호환성**: 현재 캐시 형식과 100% 호환
4. **교환 가능한 데이터 소스**: Bitget/Binance 선택 가능

### 2.2 성공 기준

- [ ] Binance에서 BTCUSDT 1h 데이터 5년치 다운로드 성공
- [ ] 기존 백테스트 시스템과 100% 호환
- [ ] 다운로드 시간 50% 이상 단축
- [ ] 에러 없이 10개 심볼 x 4개 타임프레임 수집

---

## 3. 세부 작업 계획

### Phase 1: Binance REST 클라이언트 구현 (필수)

#### 3.1.1 새 파일 생성: `backend/src/services/binance_rest.py`

```python
"""
Binance REST API 클라이언트
- 캔들 데이터 조회 전용 (인증 불필요)
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BinanceRestClient:
    """Binance Futures REST API 클라이언트 (캔들 데이터 전용)"""

    # Binance Futures API 엔드포인트
    BASE_URL = "https://fapi.binance.com"
    KLINES_ENDPOINT = "/fapi/v1/klines"

    # 타임프레임 매핑
    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1d",
        "1D": "1d",
        "1w": "1w",
        "1W": "1w",
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1500,
    ) -> List[Dict[str, Any]]:
        """
        캔들 데이터 조회 (단일 요청)

        Args:
            symbol: 거래쌍 (예: BTCUSDT)
            interval: 캔들 간격 (1m, 5m, 15m, 30m, 1h, 4h, 1d 등)
            start_time: 시작 시간 (ms, 선택)
            end_time: 종료 시간 (ms, 선택)
            limit: 조회 개수 (최대 1500)

        Returns:
            캔들 데이터 리스트
        """
        await self._ensure_session()

        # 타임프레임 변환
        binance_interval = self.INTERVAL_MAP.get(interval, interval)

        params = {
            "symbol": symbol,
            "interval": binance_interval,
            "limit": min(limit, 1500),
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        url = f"{self.BASE_URL}{self.KLINES_ENDPOINT}"

        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 429:
                    logger.warning("Binance Rate Limit 도달")
                    raise Exception("Rate Limit Exceeded")

                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Binance API 에러: {response.status} - {text}")
                    raise Exception(f"API Error: {response.status}")

                data = await response.json()

                # 캔들 데이터 파싱
                candles = []
                for kline in data:
                    candles.append({
                        "timestamp": int(kline[0]),
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5]),
                    })

                return candles

        except asyncio.TimeoutError:
            logger.error("Binance API timeout")
            raise

    async def get_all_historical_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        max_candles: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        전체 과거 캔들 데이터 조회 (페이지네이션)

        Args:
            symbol: 거래쌍 (예: BTCUSDT)
            interval: 캔들 간격
            start_time: 시작 날짜 (YYYY-MM-DD)
            end_time: 종료 날짜 (YYYY-MM-DD)
            max_candles: 최대 캔들 수 제한

        Returns:
            캔들 데이터 리스트 (오래된 것부터)
        """
        # Binance Futures 런칭일 (2019년 9월)
        BINANCE_FUTURES_LAUNCH = "2019-09-01"

        if not start_time:
            start_time = BINANCE_FUTURES_LAUNCH

        if not end_time:
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        start_dt = datetime.strptime(start_time, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_time, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )

        now_utc = datetime.now(timezone.utc)
        if end_dt > now_utc:
            end_dt = now_utc

        logger.info(f"📊 Binance에서 {symbol} ({interval}) 캔들 수집 시작")
        logger.info(f"   기간: {start_time} ~ {end_time}")

        all_candles = []
        current_start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)
        batch_count = 0
        rate_limit_delay = 0.1  # 100ms 딜레이

        while current_start_ts < end_ts:
            batch_count += 1

            try:
                candles = await self.get_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start_ts,
                    end_time=end_ts,
                    limit=1500,
                )

                if not candles:
                    break

                # 중복 제거 후 추가
                existing_ts = {c["timestamp"] for c in all_candles}
                new_candles = [c for c in candles if c["timestamp"] not in existing_ts]
                all_candles.extend(new_candles)

                # 진행률 로깅
                if batch_count % 10 == 0:
                    logger.info(f"   배치 {batch_count}: {len(all_candles)}개 수집 완료...")

                # 다음 배치 시작점
                latest_ts = max(c["timestamp"] for c in candles)
                current_start_ts = latest_ts + 1

                # 최대 캔들 수 체크
                if max_candles and len(all_candles) >= max_candles:
                    all_candles = all_candles[:max_candles]
                    break

                # Rate Limit 방지
                await asyncio.sleep(rate_limit_delay)

            except Exception as e:
                logger.error(f"   배치 {batch_count} 에러: {e}")
                break

        # 시간순 정렬
        all_candles.sort(key=lambda x: x["timestamp"])

        logger.info(f"✅ 총 {len(all_candles)}개 캔들 수집 완료 ({batch_count}회 API 호출)")

        return all_candles
```

### Phase 2: 캔들 캐시 매니저 확장

#### 3.2.1 파일 수정: `backend/src/services/candle_cache.py`

**변경 사항:**

1. 데이터 소스 선택 옵션 추가 (`source: "bitget" | "binance"`)
2. `_fetch_from_binance()` 메서드 추가
3. `_fetch_from_api()` 메서드를 소스별 분기로 수정

```python
# 추가할 내용 (candle_cache.py)

class CandleCacheManager:
    # ... 기존 코드 ...

    async def _fetch_from_api(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        source: str = "binance",  # 기본값 변경: bitget → binance
    ) -> List[Dict]:
        """
        API에서 캔들 데이터 가져오기

        Args:
            source: "binance" 또는 "bitget"
        """
        if source == "binance":
            return await self._fetch_from_binance(symbol, timeframe, start_date, end_date)
        else:
            return await self._fetch_from_bitget(symbol, timeframe, start_date, end_date)

    async def _fetch_from_binance(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict]:
        """Binance API에서 캔들 데이터 가져오기"""
        from .binance_rest import BinanceRestClient

        async with self._rate_limit_lock:
            elapsed = time.time() - self._last_api_call
            if elapsed < self._min_api_interval:
                await asyncio.sleep(self._min_api_interval - elapsed)

            try:
                client = BinanceRestClient()
                candles = await client.get_all_historical_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=start_date,
                    end_time=end_date,
                )
                await client.close()
                self._last_api_call = time.time()

                logger.info(f"   🌐 Binance에서 {len(candles)}개 캔들 수집 완료")
                return candles

            except Exception as e:
                logger.error(f"Binance API 에러: {e}")
                raise

    async def _fetch_from_bitget(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict]:
        """Bitget API에서 캔들 데이터 가져오기 (기존 로직)"""
        from .bitget_rest import BitgetRestClient

        async with self._rate_limit_lock:
            elapsed = time.time() - self._last_api_call
            if elapsed < self._min_api_interval:
                await asyncio.sleep(self._min_api_interval - elapsed)

            try:
                client = BitgetRestClient()
                candles = await client.get_all_historical_candles(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=start_date,
                    end_time=end_date,
                )
                self._last_api_call = time.time()

                logger.info(f"   🌐 Bitget에서 {len(candles)}개 캔들 수집 완료")
                return candles

            except Exception as e:
                logger.error(f"Bitget API 에러: {e}")
                raise
```

### Phase 3: 다운로드 스크립트 업데이트

#### 3.3.1 새 파일 생성: `backend/download_binance_data.py`

```python
#!/usr/bin/env python3
"""
Binance 과거 캔들 데이터 다운로드 스크립트

바이낸스 API를 사용하여 더 많은 히스토리 데이터를 빠르게 수집합니다.
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.binance_rest import BinanceRestClient
from src.services.candle_cache import CandleCacheManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("binance_download.log")],
)
logger = logging.getLogger(__name__)

# 코인별 바이낸스 선물 상장일
COIN_START_DATES = {
    "BTCUSDT": "2019-09-08",
    "ETHUSDT": "2019-11-08",
    "XRPUSDT": "2020-01-06",
    "SOLUSDT": "2021-06-17",
    "DOGEUSDT": "2021-04-19",
    "ADAUSDT": "2020-04-16",
    "AVAXUSDT": "2021-09-16",
    "LINKUSDT": "2020-02-03",
    "DOTUSDT": "2020-08-18",
    "MATICUSDT": "2021-02-22",
}


async def download_from_binance(
    symbols: list,
    timeframes: list,
    start_date: str = None,
):
    """바이낸스에서 캔들 데이터 다운로드"""

    cache = CandleCacheManager()
    client = BinanceRestClient()

    total = len(symbols) * len(timeframes)
    completed = 0
    success_data = []
    failed = []

    end_date = datetime.now().strftime("%Y-%m-%d")

    logger.info("=" * 70)
    logger.info("🚀 Binance 캔들 데이터 다운로드")
    logger.info("=" * 70)
    logger.info(f"💰 코인: {', '.join(symbols)}")
    logger.info(f"⏱️ 타임프레임: {', '.join(timeframes)}")
    logger.info("=" * 70)

    start_time = datetime.now()

    for symbol in symbols:
        coin_start = COIN_START_DATES.get(symbol, "2020-01-01")
        actual_start = start_date or coin_start

        for timeframe in timeframes:
            completed += 1
            progress = f"[{completed}/{total}]"

            logger.info(f"{progress} 📥 {symbol} {timeframe} ({actual_start} ~ {end_date})")

            try:
                candles = await client.get_all_historical_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=actual_start,
                    end_time=end_date,
                )

                if candles:
                    # 캐시에 저장
                    cache._save_to_file_cache(symbol, timeframe, candles)
                    count = len(candles)
                    logger.info(f"{progress} ✅ {symbol} {timeframe}: {count:,}개 캔들")
                    success_data.append((symbol, timeframe, count))
                else:
                    logger.warning(f"{progress} ⚠️ {symbol} {timeframe}: 데이터 없음")

            except Exception as e:
                logger.error(f"{progress} ❌ {symbol} {timeframe} 실패: {e}")
                failed.append((symbol, timeframe, str(e)))

            # Rate Limit 방지
            await asyncio.sleep(0.5)

        await asyncio.sleep(1)

    await client.close()

    # 완료 리포트
    elapsed = datetime.now() - start_time

    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 다운로드 완료 리포트")
    logger.info("=" * 70)
    logger.info(f"✅ 성공: {len(success_data)}/{total}")
    logger.info(f"❌ 실패: {len(failed)}/{total}")
    logger.info(f"⏱️ 소요 시간: {elapsed}")

    if success_data:
        total_candles = sum(c for _, _, c in success_data)
        logger.info(f"📊 총 캔들: {total_candles:,}개")

    if failed:
        logger.info("")
        logger.info("❌ 실패 목록:")
        for symbol, timeframe, error in failed:
            logger.info(f"   - {symbol} {timeframe}: {error[:50]}...")

    cache_info = cache.get_cache_info()
    logger.info(f"💾 캐시 디렉토리: {cache_info['cache_dir']}")
    logger.info("=" * 70)

    return len(failed) == 0


async def download_btc_eth_full():
    """BTC, ETH 전체 기간 다운로드"""
    return await download_from_binance(
        symbols=["BTCUSDT", "ETHUSDT"],
        timeframes=["1h", "4h", "1d"],
    )


async def download_all_coins():
    """모든 메이저 코인 다운로드"""
    return await download_from_binance(
        symbols=list(COIN_START_DATES.keys()),
        timeframes=["1h", "4h"],
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Binance 캔들 데이터 다운로드")
    parser.add_argument("--btc-eth", action="store_true", help="BTC, ETH만 다운로드")
    parser.add_argument("--all", action="store_true", help="모든 메이저 코인 다운로드")

    args = parser.parse_args()

    if args.btc_eth:
        success = asyncio.run(download_btc_eth_full())
        sys.exit(0 if success else 1)
    elif args.all:
        success = asyncio.run(download_all_coins())
        sys.exit(0 if success else 1)
    else:
        print("사용법:")
        print("  python3 download_binance_data.py --btc-eth   # BTC, ETH만")
        print("  python3 download_binance_data.py --all       # 모든 메이저 코인")
        sys.exit(0)
```

---

## 4. 구현 상세

### 4.1 파일 변경 요약

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `backend/src/services/binance_rest.py` | 🆕 신규 | Binance REST API 클라이언트 |
| `backend/src/services/candle_cache.py` | ⚠️ 수정 | Binance/Bitget 선택 로직 추가 |
| `backend/download_binance_data.py` | 🆕 신규 | Binance 다운로드 스크립트 |

### 4.2 API 상세 스펙

#### Binance Futures Klines API

```
GET https://fapi.binance.com/fapi/v1/klines

Parameters:
- symbol (필수): 거래쌍 (예: BTCUSDT)
- interval (필수): 캔들 간격 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- startTime (선택): 시작 시간 (ms)
- endTime (선택): 종료 시간 (ms)
- limit (선택): 반환 개수 (기본 500, 최대 1500)

Response (배열):
[
  [
    1499040000000,      // Open time (ms)
    "0.01634000",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore
  ]
]
```

### 4.3 Rate Limit 전략

| 거래소 | 제한 | 권장 딜레이 |
|--------|------|------------|
| Binance | 1200/min | 50-100ms |
| Bitget | 20/sec | 200-300ms |

---

## 5. 테스트 계획

### 5.1 유닛 테스트

```python
# tests/test_binance_rest.py

import pytest
from src.services.binance_rest import BinanceRestClient

@pytest.mark.asyncio
async def test_get_klines_btc():
    """BTC 캔들 데이터 조회 테스트"""
    client = BinanceRestClient()
    candles = await client.get_klines(
        symbol="BTCUSDT",
        interval="1h",
        limit=100
    )
    await client.close()

    assert len(candles) > 0
    assert "timestamp" in candles[0]
    assert "open" in candles[0]
    assert "high" in candles[0]
    assert "low" in candles[0]
    assert "close" in candles[0]
    assert "volume" in candles[0]


@pytest.mark.asyncio
async def test_get_all_historical_klines():
    """전체 히스토리 조회 테스트"""
    client = BinanceRestClient()
    candles = await client.get_all_historical_klines(
        symbol="BTCUSDT",
        interval="1d",
        start_time="2024-01-01",
        end_time="2024-01-31",
    )
    await client.close()

    assert len(candles) >= 30
    # 시간순 정렬 확인
    timestamps = [c["timestamp"] for c in candles]
    assert timestamps == sorted(timestamps)
```

### 5.2 통합 테스트

```bash
# 1. 단일 심볼 테스트
cd backend
python3 -c "
import asyncio
from src.services.binance_rest import BinanceRestClient

async def test():
    client = BinanceRestClient()
    candles = await client.get_klines('BTCUSDT', '1h', limit=10)
    print(f'Fetched {len(candles)} candles')
    print(candles[0])
    await client.close()

asyncio.run(test())
"

# 2. 다운로드 스크립트 테스트 (BTC, ETH만)
python3 download_binance_data.py --btc-eth
```

### 5.3 백테스트 호환성 테스트

```python
# 바이낸스 데이터로 백테스트 실행
from src.services.grid_backtester import GridBacktester
from src.database.models import GridMode, PositionDirection
from decimal import Decimal

async def test_backtest_with_binance_data():
    backtester = GridBacktester()
    result = await backtester.run_backtest(
        symbol="BTCUSDT",
        direction=PositionDirection.LONG,
        lower_price=Decimal("90000"),
        upper_price=Decimal("100000"),
        grid_count=10,
        grid_mode=GridMode.ARITHMETIC,
        leverage=5,
        investment=Decimal("1000"),
        days=30,
        granularity="1h"
    )
    print(f"ROI: {result.roi_30d}%")
    print(f"Trades: {result.total_trades}")
```

---

## 6. 롤백 전략

### 6.1 롤백 시나리오

Binance API에 문제가 발생할 경우:

```python
# candle_cache.py에서 source 파라미터만 변경
candles = await cache.get_candles(
    symbol="BTCUSDT",
    timeframe="1h",
    start_date="2024-01-01",
    end_date="2024-12-01",
    source="bitget"  # binance → bitget
)
```

### 6.2 데이터 백업

```bash
# 기존 캐시 백업
cp -r backend/candle_cache backend/candle_cache_backup_$(date +%Y%m%d)
```

---

## 📝 체크리스트

### Phase 1: Binance REST 클라이언트

- [ ] `binance_rest.py` 파일 생성
- [ ] `get_klines()` 메서드 구현
- [ ] `get_all_historical_klines()` 메서드 구현
- [ ] 단위 테스트 통과

### Phase 2: 캔들 캐시 매니저 확장

- [ ] `candle_cache.py`에 Binance 지원 추가
- [ ] 소스 선택 로직 구현
- [ ] 기존 기능 호환성 테스트

### Phase 3: 다운로드 스크립트

- [ ] `download_binance_data.py` 생성
- [ ] BTC, ETH 다운로드 테스트
- [ ] 전체 코인 다운로드 테스트

### Phase 4: 검증

- [ ] 백테스트 호환성 확인
- [ ] 데이터 품질 검증
- [ ] 성능 비교 (Bitget vs Binance)

---

## 🚀 실행 가이드

### 빠른 시작

```bash
# 1. backend 디렉토리로 이동
cd backend

# 2. (옵션) 기존 캐시 백업
cp -r candle_cache candle_cache_backup

# 3. Binance에서 BTC, ETH 다운로드
python3 download_binance_data.py --btc-eth

# 4. (옵션) 모든 메이저 코인 다운로드
python3 download_binance_data.py --all

# 5. 캐시 상태 확인
cat candle_cache/cache_metadata.json | python3 -m json.tool
```

---

> **다음 작업자 안내**
> 이 문서를 기반으로 구현을 진행하시면 됩니다.
> 질문이나 문제가 있으면 이 문서를 업데이트해 주세요.
