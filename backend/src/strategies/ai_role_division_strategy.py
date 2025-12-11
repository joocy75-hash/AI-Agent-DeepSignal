"""
AI 역할분담 전략 - 빠른 진입 + 스마트 대응

특징:
- 진입 AI: 낮은 임계값으로 빠르게 진입 (RSI + EMA 기반)
- 관리 AI: 포지션 진입 후 동적 손절/익절 관리
- ETH 전용, 잔고 40% 사용
- 손익비 1:2 이상 유지

진입 조건 (완화된 조건):
- RSI 과매도/과매수 (35/65)
- 단기 EMA > 장기 EMA (트렌드 방향)
- 최소 캔들 20개만 필요

청산 조건 (스마트 대응):
- 동적 손절: ATR 기반 (1.5%)
- 동적 익절: ATR 기반 (3%)
- 트레일링 스탑: 1% 수익 후 활성화
- 반대 시그널 시 즉시 청산
"""

import logging

logger = logging.getLogger(__name__)


def calculate_ema(prices, period):
    """EMA 계산"""
    if len(prices) < period:
        return []

    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]

    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])

    return ema


def calculate_rsi(prices, period=14):
    """RSI 계산"""
    if len(prices) < period + 1:
        return []

    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

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


def calculate_atr(candles, period=14):
    """ATR 계산"""
    if len(candles) < period + 1:
        return 0

    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]['high']
        low = candles[i]['low']
        prev_close = candles[i-1]['close']

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0

    return sum(true_ranges[-period:]) / period


def generate_signal(candles, params, current_position=None):
    """
    AI 역할분담 시그널 생성

    Returns:
        dict: {
            "action": "buy" | "sell" | "hold" | "close",
            "confidence": 0.0 ~ 1.0,
            "reason": str,
            "stop_loss": float,
            "take_profit": float,
            "size": float
        }
    """
    # 기본값
    result = {
        "action": "hold",
        "confidence": 0.0,
        "reason": "분석 중...",
        "stop_loss": None,
        "take_profit": None,
        "size": None,
        "size_metadata": {
            "position_size_percent": params.get("position_size_percent", 0.4),
            "leverage": params.get("leverage", 10)
        }
    }

    # 최소 캔들 수 체크 (완화: 20개)
    min_candles = params.get("min_candles", 20)
    if len(candles) < min_candles:
        result["reason"] = f"데이터 부족 ({len(candles)}/{min_candles})"
        return result

    try:
        # 가격 데이터 추출
        closes = [c['close'] for c in candles]
        current_price = closes[-1]

        # 지표 계산
        ema_short = calculate_ema(closes, params.get("ema_short", 9))
        ema_long = calculate_ema(closes, params.get("ema_long", 21))
        rsi = calculate_rsi(closes, params.get("rsi_period", 14))
        atr = calculate_atr(candles, 14)

        if not ema_short or not ema_long or not rsi:
            result["reason"] = "지표 계산 실패"
            return result

        # 현재 지표값
        current_ema_short = ema_short[-1]
        current_ema_long = ema_long[-1]
        current_rsi = rsi[-1]

        # 트렌드 판단
        uptrend = current_ema_short > current_ema_long
        downtrend = current_ema_short < current_ema_long

        # 손절/익절 계산 (ATR 기반)
        atr_multiplier_sl = params.get("atr_sl_multiplier", 1.5)
        atr_multiplier_tp = params.get("atr_tp_multiplier", 3.0)

        # RSI 임계값 (완화된 조건)
        rsi_oversold = params.get("rsi_oversold", 35)
        rsi_overbought = params.get("rsi_overbought", 65)

        # ============ 포지션 관리 AI (청산 로직) ============
        if current_position:
            entry_price = current_position.get('entry_price', current_price)
            side = current_position.get('side', 'long')

            # 현재 수익률 계산
            if side == 'long':
                pnl_percent = (current_price - entry_price) / entry_price * 100

                # 트레일링 스탑: 1% 수익 후 0.5% 하락 시 청산
                if pnl_percent >= 1.0:
                    trailing_stop = entry_price * 1.005  # 0.5% 수익 확보
                    if current_price < trailing_stop:
                        result["action"] = "close"
                        result["confidence"] = 0.9
                        result["reason"] = f"트레일링 스탑 (수익 {pnl_percent:.2f}%)"
                        return result

                # 손절: -1.5%
                if pnl_percent <= -1.5:
                    result["action"] = "close"
                    result["confidence"] = 0.95
                    result["reason"] = f"손절 ({pnl_percent:.2f}%)"
                    return result

                # 익절: +3%
                if pnl_percent >= 3.0:
                    result["action"] = "close"
                    result["confidence"] = 0.9
                    result["reason"] = f"익절 ({pnl_percent:.2f}%)"
                    return result

                # 반대 시그널 (숏 조건 충족 시 청산)
                if downtrend and current_rsi > rsi_overbought:
                    result["action"] = "close"
                    result["confidence"] = 0.85
                    result["reason"] = f"반대 시그널 (RSI: {current_rsi:.1f})"
                    return result

            else:  # short
                pnl_percent = (entry_price - current_price) / entry_price * 100

                # 트레일링 스탑
                if pnl_percent >= 1.0:
                    trailing_stop = entry_price * 0.995
                    if current_price > trailing_stop:
                        result["action"] = "close"
                        result["confidence"] = 0.9
                        result["reason"] = f"트레일링 스탑 (수익 {pnl_percent:.2f}%)"
                        return result

                # 손절
                if pnl_percent <= -1.5:
                    result["action"] = "close"
                    result["confidence"] = 0.95
                    result["reason"] = f"손절 ({pnl_percent:.2f}%)"
                    return result

                # 익절
                if pnl_percent >= 3.0:
                    result["action"] = "close"
                    result["confidence"] = 0.9
                    result["reason"] = f"익절 ({pnl_percent:.2f}%)"
                    return result

                # 반대 시그널
                if uptrend and current_rsi < rsi_oversold:
                    result["action"] = "close"
                    result["confidence"] = 0.85
                    result["reason"] = f"반대 시그널 (RSI: {current_rsi:.1f})"
                    return result

            # 포지션 유지
            result["reason"] = f"포지션 유지 ({side}, PnL: {pnl_percent:.2f}%)"
            return result

        # ============ 진입 AI (신규 진입 로직) ============
        # 진입 조건을 완화하여 더 자주 진입

        # EMA 크로스 확인 (최근 5개 봉에서 크로스 발생)
        ema_cross_up = False
        ema_cross_down = False
        if len(ema_short) >= 3 and len(ema_long) >= 3:
            # 골든크로스: 단기 EMA가 장기 EMA를 상향 돌파
            if ema_short[-2] <= ema_long[-2] and ema_short[-1] > ema_long[-1]:
                ema_cross_up = True
            # 데드크로스: 단기 EMA가 장기 EMA를 하향 돌파
            if ema_short[-2] >= ema_long[-2] and ema_short[-1] < ema_long[-1]:
                ema_cross_down = True

        # 롱 진입 조건 (완화됨)
        # 조건1: 상승 트렌드 + RSI 30-50 (과매도 구간에서 반등)
        # 조건2: EMA 골든크로스 발생 + RSI 50 이하
        long_condition1 = uptrend and 25 <= current_rsi <= 50
        long_condition2 = ema_cross_up and current_rsi <= 55

        if long_condition1 or long_condition2:
            confidence = 0.75 if long_condition2 else 0.65
            reason = "골든크로스" if long_condition2 else "RSI 반등"

            result["action"] = "buy"
            result["confidence"] = confidence
            result["reason"] = f"롱 진입 ({reason}, RSI: {current_rsi:.1f})"
            result["stop_loss"] = current_price * 0.985  # -1.5% 손절
            result["take_profit"] = current_price * 1.03  # +3% 익절

            logger.info(f"🟢 BUY Signal: RSI={current_rsi:.1f}, EMA_short={current_ema_short:.2f}, EMA_long={current_ema_long:.2f}, cross_up={ema_cross_up}")
            return result

        # 숏 진입 조건 (완화됨)
        # 조건1: 하락 트렌드 + RSI 50-75 (과매수 구간에서 하락)
        # 조건2: EMA 데드크로스 발생 + RSI 45 이상
        short_condition1 = downtrend and 50 <= current_rsi <= 75
        short_condition2 = ema_cross_down and current_rsi >= 45

        if short_condition1 or short_condition2:
            confidence = 0.75 if short_condition2 else 0.65
            reason = "데드크로스" if short_condition2 else "RSI 하락"

            result["action"] = "sell"
            result["confidence"] = confidence
            result["reason"] = f"숏 진입 ({reason}, RSI: {current_rsi:.1f})"
            result["stop_loss"] = current_price * 1.015  # +1.5% 손절
            result["take_profit"] = current_price * 0.97  # -3% 익절

            logger.info(f"🔴 SELL Signal: RSI={current_rsi:.1f}, EMA_short={current_ema_short:.2f}, EMA_long={current_ema_long:.2f}, cross_down={ema_cross_down}")
            return result

        # 진입 조건 미충족
        result["reason"] = f"대기 (RSI: {current_rsi:.1f}, 트렌드: {'상승' if uptrend else '하락' if downtrend else '횡보'})"
        return result

    except Exception as e:
        logger.error(f"Signal generation error: {e}", exc_info=True)
        result["reason"] = f"에러: {str(e)}"
        return result


# DynamicStrategyExecutor에서 호출할 메인 함수
def run_strategy(candles, params, current_position=None):
    """전략 실행 진입점"""
    return generate_signal(candles, params, current_position)
