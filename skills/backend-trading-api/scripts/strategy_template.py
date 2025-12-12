"""
전략 템플릿: {STRATEGY_NAME}

특징:
- 타임프레임: 1h, 4h
- 진입 조건: {ENTRY_CONDITIONS}
- 손익비: 1:2

기본 파라미터:
- rsi_period: 14
- macd_fast: 12
- macd_slow: 26
- macd_signal: 9
- stop_loss_percent: 2.0
- take_profit_percent: 4.0
- position_size_percent: 30
- leverage: 5
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기술 지표 계산 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def calculate_rsi(candles: list, period: int = 14) -> list:
    """RSI 계산"""
    if len(candles) < period + 1:
        return []

    closes = [c["close"] for c in candles]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))

    return rsi_values


def calculate_ema(candles: list, period: int) -> list:
    """EMA 계산"""
    if len(candles) < period:
        return []

    closes = [c["close"] for c in candles]
    multiplier = 2 / (period + 1)

    ema = [sum(closes[:period]) / period]

    for price in closes[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])

    return ema


def calculate_sma(candles: list, period: int) -> list:
    """SMA 계산"""
    if len(candles) < period:
        return []

    closes = [c["close"] for c in candles]
    sma = []

    for i in range(period - 1, len(closes)):
        sma.append(sum(closes[i - period + 1 : i + 1]) / period)

    return sma


def calculate_macd(
    candles: list, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple:
    """MACD 계산"""
    if len(candles) < slow + signal:
        return [], [], []

    ema_fast = calculate_ema(candles, fast)
    ema_slow = calculate_ema(candles, slow)

    # MACD 라인 = 단기 EMA - 장기 EMA
    offset = slow - fast
    macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]

    # 시그널 라인 = MACD의 EMA
    if len(macd_line) < signal:
        return macd_line, [], []

    multiplier = 2 / (signal + 1)
    signal_line = [sum(macd_line[:signal]) / signal]

    for val in macd_line[signal:]:
        signal_line.append((val - signal_line[-1]) * multiplier + signal_line[-1])

    # 히스토그램 = MACD - 시그널
    offset = len(macd_line) - len(signal_line)
    histogram = [macd_line[i + offset] - signal_line[i] for i in range(len(signal_line))]

    return macd_line[-len(signal_line) :], signal_line, histogram


def calculate_bollinger_bands(candles: list, period: int = 20, std_dev: float = 2.0) -> tuple:
    """볼린저밴드 계산"""
    if len(candles) < period:
        return [], [], []

    closes = [c["close"] for c in candles]
    sma = calculate_sma(candles, period)

    upper = []
    lower = []

    for i in range(len(sma)):
        idx = i + period - 1
        variance = sum((closes[j] - sma[i]) ** 2 for j in range(idx - period + 1, idx + 1)) / period
        std = variance ** 0.5
        upper.append(sma[i] + std_dev * std)
        lower.append(sma[i] - std_dev * std)

    return upper, sma, lower


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전략 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def calculate_position_size(balance: float, params: dict) -> float:
    """
    포지션 크기 계산

    Args:
        balance: 현재 잔고 (USDT)
        params: 전략 파라미터

    Returns:
        포지션 크기 (USDT)
    """
    percent = params.get("position_size_percent", 30) / 100
    leverage = params.get("leverage", 5)
    return balance * percent * leverage


def check_entry_signal(candles: list, params: dict) -> str | None:
    """
    진입 시그널 체크

    Args:
        candles: OHLCV 캔들 리스트
            [{"timestamp": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]
        params: 전략 파라미터

    Returns:
        'LONG' | 'SHORT' | None
    """
    # 최소 캔들 수 확인
    min_candles = max(
        params.get("rsi_period", 14) + 10,
        params.get("macd_slow", 26) + params.get("macd_signal", 9) + 10,
    )

    if len(candles) < min_candles:
        return None

    try:
        # 지표 계산
        rsi = calculate_rsi(candles, params.get("rsi_period", 14))
        macd, signal, hist = calculate_macd(
            candles,
            params.get("macd_fast", 12),
            params.get("macd_slow", 26),
            params.get("macd_signal", 9),
        )

        # 데이터 검증
        if len(rsi) < 2 or len(macd) < 2:
            return None

        # 파라미터
        rsi_oversold = params.get("rsi_oversold", 30)
        rsi_overbought = params.get("rsi_overbought", 70)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TODO: 진입 조건 구현
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # 롱 진입 조건 예시:
        # - RSI 과매도 (< 30)
        # - MACD 골든크로스 (MACD > Signal)
        if rsi[-1] < rsi_oversold and macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
            return "LONG"

        # 숏 진입 조건 예시:
        # - RSI 과매수 (> 70)
        # - MACD 데드크로스 (MACD < Signal)
        if rsi[-1] > rsi_overbought and macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
            return "SHORT"

        return None

    except Exception as e:
        print(f"Error in check_entry_signal: {e}")
        return None


def calculate_stop_loss(entry_price: float, side: str, params: dict) -> float:
    """
    손절가 계산

    Args:
        entry_price: 진입가
        side: 'LONG' or 'SHORT'
        params: 전략 파라미터

    Returns:
        손절가
    """
    sl_percent = params.get("stop_loss_percent", 2.0) / 100

    if side == "LONG":
        return entry_price * (1 - sl_percent)
    else:
        return entry_price * (1 + sl_percent)


def calculate_take_profit(entry_price: float, side: str, params: dict) -> float:
    """
    익절가 계산

    Args:
        entry_price: 진입가
        side: 'LONG' or 'SHORT'
        params: 전략 파라미터

    Returns:
        익절가
    """
    tp_percent = params.get("take_profit_percent", 4.0) / 100

    if side == "LONG":
        return entry_price * (1 + tp_percent)
    else:
        return entry_price * (1 - tp_percent)


def should_partial_exit(position: dict, current_price: float, candles: list, params: dict) -> tuple:
    """
    부분 청산 판단

    Args:
        position: 현재 포지션 정보
        current_price: 현재가
        candles: 캔들 데이터
        params: 전략 파라미터

    Returns:
        (should_exit: bool, exit_ratio: float)
        - should_exit: 부분 청산 여부
        - exit_ratio: 청산 비율 (0.0 ~ 1.0)
    """
    # TODO: 부분 청산 로직 구현
    # 예: RSI가 중립구간(40-60)으로 복귀 시 50% 청산

    try:
        rsi = calculate_rsi(candles, 14)
        if len(rsi) < 1:
            return False, 0

        if 40 <= rsi[-1] <= 60:
            return True, 0.5

        return False, 0
    except:
        return False, 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


if __name__ == "__main__":
    # 샘플 캔들 데이터로 테스트
    sample_candles = [
        {"timestamp": i, "open": 100 + i * 0.1, "high": 101 + i * 0.1, "low": 99 + i * 0.1, "close": 100 + i * 0.15, "volume": 1000}
        for i in range(100)
    ]

    params = {
        "rsi_period": 14,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 4.0,
    }

    signal = check_entry_signal(sample_candles, params)
    print(f"Signal: {signal}")

    if signal:
        entry_price = sample_candles[-1]["close"]
        sl = calculate_stop_loss(entry_price, signal, params)
        tp = calculate_take_profit(entry_price, signal, params)
        print(f"Entry: {entry_price:.2f}, SL: {sl:.2f}, TP: {tp:.2f}")
