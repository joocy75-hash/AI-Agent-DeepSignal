# 거래소 API 연동 참조

## Bitget REST API

### 클라이언트 초기화

```python
from ..services.bitget_rest import get_bitget_rest, BitgetRestClient

# 싱글톤 캐싱 사용 (권장)
client = get_bitget_rest(api_key, api_secret, passphrase)

# 직접 생성
client = BitgetRestClient(api_key, api_secret, passphrase)
```

### 계좌 관리

```python
# 계좌 정보 조회
account_info = await client.get_account_info(product_type="USDT-FUTURES")
# Returns: {"accountEquity": "1000.00", "available": "800.00", "locked": "200.00", ...}

# 잔고 조회 (CCXT 호환 형식)
balance = await client.fetch_balance()
# Returns: {"USDT": {"free": 800.0, "used": 200.0, "total": 1000.0}}

# 포지션 조회
positions = await client.get_positions(product_type="USDT-FUTURES")
# Returns: [{"symbol": "BTCUSDT", "total": "0.01", "holdSide": "long", ...}, ...]

# 특정 포지션 조회
position = await client.get_single_position(symbol="BTCUSDT", margin_coin="USDT")
```

### 주문 실행

```python
from ..services.bitget_rest import OrderSide, OrderType, PositionSide

# 시장가 주문 (롱)
result = await client.place_market_order(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    size=0.001,
    margin_coin="USDT",
)
# Returns: {"orderId": "123456", "clientOid": "..."}

# 시장가 주문 (숏)
result = await client.place_market_order(
    symbol="BTCUSDT",
    side=OrderSide.SELL,
    size=0.001,
    margin_coin="USDT",
)

# 지정가 주문
result = await client.place_limit_order(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    size=0.001,
    price=50000.0,
    margin_coin="USDT",
)

# 포지션 청산 (reduce_only)
result = await client.place_market_order(
    symbol="BTCUSDT",
    side=OrderSide.SELL,  # 롱 청산은 SELL
    size=0.001,
    margin_coin="USDT",
    reduce_only=True,
)
```

### 주문 관리

```python
# 주문 취소
await client.cancel_order(
    symbol="BTCUSDT",
    order_id="123456",
    margin_coin="USDT"
)

# 모든 주문 취소
await client.cancel_all_orders(symbol="BTCUSDT", margin_coin="USDT")

# 미체결 주문 조회
open_orders = await client.get_open_orders(symbol="BTCUSDT")

# 주문 히스토리 조회
history = await client.get_order_history(
    symbol="BTCUSDT",
    start_time=1704067200000,  # ms timestamp
    end_time=1704153600000,
    limit=100
)
```

### 포지션 관리

```python
# 포지션 청산
result = await client.close_position(
    symbol="BTCUSDT",
    side=PositionSide.LONG,
    margin_coin="USDT",
)

# 레버리지 설정
await client.set_leverage(symbol="BTCUSDT", leverage=10)

# 포지션 모드 설정
await client.set_position_mode(
    product_type="USDT-FUTURES",
    hold_mode="double_hold"  # or "single_hold"
)
```

### 시장 데이터

```python
# 현재가 조회
ticker = await client.get_ticker(symbol="BTCUSDT")
# Returns: {"lastPr": "50000.00", "bidPr": "49999.00", "askPr": "50001.00", ...}

# 호가 조회
orderbook = await client.get_orderbook(symbol="BTCUSDT", limit=100)

# 캔들 데이터 조회 (단일 요청, 최대 1000개)
candles = await client.get_historical_candles(
    symbol="BTCUSDT",
    interval="1h",
    start_time="2024-01-01",
    end_time="2024-01-31",
    limit=1000
)

# 전체 과거 데이터 조회 (페이지네이션, 무제한)
all_candles = await client.get_all_historical_candles(
    symbol="BTCUSDT",
    interval="1h",
    start_time="2023-01-01",
    end_time="2024-01-01",
    max_candles=50000
)
```

---

## API 서명 생성

```python
import hmac
import hashlib
import base64
import time

def generate_signature(api_secret: str, timestamp: str, method: str, request_path: str, body: str = "") -> str:
    """
    Bitget API 서명 생성

    Args:
        api_secret: API 시크릿 키
        timestamp: 밀리초 타임스탬프
        method: HTTP 메서드 (GET, POST)
        request_path: API 엔드포인트 (쿼리 파라미터 포함)
        body: 요청 바디 (POST 시)

    Returns:
        Base64 인코딩된 서명
    """
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(api_secret, encoding="utf8"),
        bytes(message, encoding="utf-8"),
        digestmod=hashlib.sha256,
    )
    return base64.b64encode(mac.digest()).decode()


def get_headers(api_key: str, api_secret: str, passphrase: str, method: str, request_path: str, body: str = "") -> dict:
    """
    Bitget API 요청 헤더 생성
    """
    timestamp = str(int(time.time() * 1000))
    sign = generate_signature(api_secret, timestamp, method, request_path, body)

    return {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
        "locale": "en-US",
    }
```

---

## 에러 처리

### 예외 클래스

```python
from ..utils.bitget_exceptions import (
    BitgetAPIError,
    BitgetRateLimitError,
    BitgetAuthenticationError,
    BitgetNetworkError,
    BitgetTimeoutError,
    classify_bitget_error,
)

# 에러 분류
exception = classify_bitget_error(error_code, error_msg)
```

### 에러 코드 매핑

| 코드 | 의미 | 예외 클래스 |
|------|------|-------------|
| 00000 | 성공 | - |
| 40001 | 잘못된 요청 | BitgetAPIError |
| 40014 | Rate Limit 초과 | BitgetRateLimitError |
| 40018 | 인증 실패 | BitgetAuthenticationError |
| 40102 | 잘못된 서명 | BitgetAuthenticationError |
| 40703 | 잔고 부족 | BitgetAPIError |

### 재시도 로직

```python
# BitgetRestClient._request()에 내장
# - max_retries: 3회
# - retry_delay: 1초 (exponential backoff)
# - Rate Limit: 60초 대기 후 재시도
# - 인증 에러: 재시도 없이 즉시 실패
```

---

## WebSocket 데이터 수집

```python
from ..services.bitget_ws_collector import BitgetWSCollector

# 채널 구독
collector = BitgetWSCollector()
await collector.connect(["trade.BTCUSDT", "candle1m.BTCUSDT"])

# 콜백 설정
collector.on_message = lambda data: process_market_data(data)
```

---

## 주의사항

1. **API 키 보안**
   - API 키는 반드시 암호화하여 저장 (Fernet)
   - 환경 변수에 직접 노출 금지

2. **Rate Limiting**
   - Bitget: 분당 100회 제한
   - 재시도 시 exponential backoff 사용

3. **주문 실행**
   - 시장가 주문 시 슬리피지 고려
   - reduce_only 플래그 사용하여 청산

4. **포지션 관리**
   - double_hold 모드에서는 롱/숏 독립 관리
   - 청산 시 반대 방향 주문 사용
