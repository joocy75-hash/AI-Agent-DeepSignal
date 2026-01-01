from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:
    from src.ml.features import FeaturePipeline
    from src.ml.models import EnsemblePredictor
    ML_AVAILABLE = True
except Exception:
    FeaturePipeline = None
    EnsemblePredictor = None
    ML_AVAILABLE = False


@dataclass
class PositionState:
    side: Optional[str] = None
    add_count: int = 0
    max_profit_percent: float = 0.0


@dataclass
class IndicatorSnapshot:
    close: float
    ema_fast: float
    ema_slow: float
    ema_trend: float
    rsi: float
    macd_hist: float
    atr_percent: float
    volume_ratio: float


class ETHAIFusionStrategy:
    def __init__(self, params: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None):
        self.params = params or {}
        self.user_id = user_id
        self.symbol = self.params.get("symbol", "ETH/USDT")
        self.timeframe = self.params.get("timeframe", "5m")
        self.enable_ml = self.params.get("enable_ml", True) and ML_AVAILABLE

        self._state = PositionState()
        self._feature_pipeline = FeaturePipeline() if self.enable_ml and FeaturePipeline else None
        self._ml_predictor = EnsemblePredictor() if self.enable_ml and EnsemblePredictor else None

        self._ema_fast = int(self.params.get("ema_fast", 9))
        self._ema_slow = int(self.params.get("ema_slow", 21))
        self._ema_trend = int(self.params.get("ema_trend", 55))
        self._rsi_length = int(self.params.get("rsi_length", 14))
        self._atr_length = int(self.params.get("atr_length", 14))
        self._entry_threshold = float(self.params.get("entry_threshold", 4.0))
        self._max_adds = int(self.params.get("max_adds", 3))
        self._add_step = float(self.params.get("add_step_percent", 0.8))
        self._add_scale = float(self.params.get("add_scale", 0.35))

    def generate_signal(
        self,
        current_price: float,
        candles: list,
        current_position: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not candles or len(candles) < 60:
            return self._hold("insufficient_candles")

        snapshot = self._compute_indicators(candles)
        ml_result = self._get_ml_prediction(candles, snapshot)

        if current_position and current_position.get("size", 0) > 0:
            return self._manage_position(current_price, snapshot, ml_result, current_position)

        self._reset_state()
        return self._evaluate_entry(snapshot, ml_result)

    def _evaluate_entry(self, snapshot: IndicatorSnapshot, ml_result: Any) -> Dict[str, Any]:
        long_score, short_score, reasons = self._score_entry(snapshot)
        action = "hold"

        if long_score >= self._entry_threshold and long_score >= short_score + 1:
            action = "buy"
        elif short_score >= self._entry_threshold and short_score >= long_score + 1:
            action = "sell"

        if action == "hold":
            return self._hold("no_entry")

        if ml_result:
            if ml_result.should_skip_entry():
                return self._hold("ml_skip")
            ml_dir = ml_result.direction.direction.value
            if ml_result.direction.confidence > 0.55 and ml_dir != ("long" if action == "buy" else "short"):
                return self._hold("ml_mismatch")
            if not ml_result.timing.is_good_entry and ml_result.timing.confidence > 0.6:
                return self._hold("timing_block")

        confidence = self._confidence_from_score(max(long_score, short_score), ml_result)
        stop_loss, take_profit = self._risk_targets(snapshot, ml_result)
        return {
            "action": action,
            "confidence": confidence,
            "reason": "; ".join(reasons) if reasons else "entry",
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size": None,
            "strategy_type": "eth_ai_fusion",
        }

    def _manage_position(
        self,
        current_price: float,
        snapshot: IndicatorSnapshot,
        ml_result: Any,
        current_position: Dict[str, Any],
    ) -> Dict[str, Any]:
        side = current_position.get("side", "long")
        entry_price = float(current_position.get("entry_price", snapshot.close))
        leverage = float(current_position.get("leverage", 1))
        raw_pnl_percent = self._pnl_percent(side, entry_price, current_price, 1)
        pnl_percent = self._pnl_percent(side, entry_price, current_price, leverage)

        self._sync_state(side, pnl_percent)
        stop_loss, take_profit = self._risk_targets(snapshot, ml_result)

        if pnl_percent <= -stop_loss:
            return self._close("stop_loss", stop_loss, take_profit)

        if self._state.max_profit_percent >= take_profit:
            trailing_floor = max(stop_loss, self._state.max_profit_percent * 0.5)
            if pnl_percent <= trailing_floor:
                return self._close("trailing_stop", stop_loss, take_profit)

        if self._should_exit_on_reversal(side, snapshot):
            return self._close("trend_reversal", stop_loss, take_profit)

        add_signal = self._check_add(side, raw_pnl_percent, snapshot, ml_result)
        if add_signal:
            add_size = max(current_position.get("size", 0) * self._add_scale, 0.0)
            return {
                "action": "buy" if side == "long" else "sell",
                "confidence": add_signal,
                "reason": "add_on_profit",
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "size": add_size,
                "strategy_type": "eth_ai_fusion",
            }

        return self._hold("manage_hold", stop_loss, take_profit)

    def _check_add(self, side: str, pnl_percent: float, snapshot: IndicatorSnapshot, ml_result: Any) -> Optional[float]:
        if self._state.add_count >= self._max_adds:
            return None
        next_add = self._add_step * (self._state.add_count + 1)
        if pnl_percent < next_add:
            return None
        if side == "long" and snapshot.rsi >= 75:
            return None
        if side == "short" and snapshot.rsi <= 25:
            return None
        if side == "long" and (snapshot.ema_fast < snapshot.ema_slow or snapshot.macd_hist < 0):
            return None
        if side == "short" and (snapshot.ema_fast > snapshot.ema_slow or snapshot.macd_hist > 0):
            return None
        if ml_result and ml_result.direction.confidence > 0.55:
            ml_dir = ml_result.direction.direction.value
            if ml_dir != ("long" if side == "long" else "short"):
                return None
        self._state.add_count += 1
        return max(0.55, self._confidence_from_score(5.0, ml_result))

    def _score_entry(self, snapshot: IndicatorSnapshot) -> Tuple[float, float, list]:
        long_score = 0.0
        short_score = 0.0
        reasons = []

        if snapshot.ema_fast > snapshot.ema_slow:
            long_score += 1
            reasons.append("ema_fast>ema_slow")
        if snapshot.ema_fast < snapshot.ema_slow:
            short_score += 1
            reasons.append("ema_fast<ema_slow")
        if snapshot.close > snapshot.ema_fast:
            long_score += 1
            reasons.append("price>ema_fast")
        if snapshot.close < snapshot.ema_fast:
            short_score += 1
            reasons.append("price<ema_fast")
        if snapshot.rsi >= 50:
            long_score += 1
        if snapshot.rsi <= 50:
            short_score += 1
        if snapshot.macd_hist > 0:
            long_score += 1
        if snapshot.macd_hist < 0:
            short_score += 1
        if snapshot.volume_ratio >= 1.05:
            long_score += 1
            short_score += 1

        return long_score, short_score, reasons

    def _risk_targets(self, snapshot: IndicatorSnapshot, ml_result: Any) -> Tuple[float, float]:
        atr_based = snapshot.atr_percent * 1.2
        stop_loss = max(0.6, min(1.6, atr_based))
        take_profit = max(1.2, min(4.5, snapshot.atr_percent * 2.4))

        if ml_result and ml_result.stoploss.confidence > 0.55:
            stop_loss = max(0.6, min(1.8, ml_result.stoploss.optimal_sl_percent))

        return stop_loss, take_profit

    def _compute_indicators(self, candles: list) -> IndicatorSnapshot:
        closes = [c.get("close", 0) for c in candles]
        highs = [c.get("high", 0) for c in candles]
        lows = [c.get("low", 0) for c in candles]
        volumes = [c.get("volume", 0) for c in candles]

        ema_fast = self._ema(closes, self._ema_fast)
        ema_slow = self._ema(closes, self._ema_slow)
        ema_trend = self._ema(closes, self._ema_trend)
        rsi = self._rsi(closes, self._rsi_length)
        macd_hist = self._macd_hist(closes)
        atr_percent = self._atr_percent(highs, lows, closes, self._atr_length)
        volume_ratio = self._volume_ratio(volumes, 20)

        return IndicatorSnapshot(
            close=closes[-1],
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            ema_trend=ema_trend,
            rsi=rsi,
            macd_hist=macd_hist,
            atr_percent=atr_percent,
            volume_ratio=volume_ratio,
        )

    def _get_ml_prediction(self, candles: list, snapshot: IndicatorSnapshot) -> Any:
        if not self._ml_predictor or not self._feature_pipeline:
            return None
        symbol = self.symbol.replace("/", "").replace(":USDT", "")
        features = self._feature_pipeline.extract_features(candles, symbol=symbol)
        if features.empty:
            return None
        rule_signal = "long" if snapshot.ema_fast > snapshot.ema_slow else "short"
        return self._ml_predictor.predict(features, symbol=symbol, rule_based_signal=rule_signal)

    def _sync_state(self, side: str, pnl_percent: float) -> None:
        if self._state.side != side:
            self._state = PositionState(side=side, add_count=0, max_profit_percent=pnl_percent)
            return
        if pnl_percent > self._state.max_profit_percent:
            self._state.max_profit_percent = pnl_percent

    def _reset_state(self) -> None:
        self._state = PositionState()

    def _pnl_percent(self, side: str, entry_price: float, current_price: float, leverage: float) -> float:
        if entry_price <= 0:
            return 0.0
        if side == "long":
            return ((current_price - entry_price) / entry_price) * 100 * leverage
        return ((entry_price - current_price) / entry_price) * 100 * leverage

    def _should_exit_on_reversal(self, side: str, snapshot: IndicatorSnapshot) -> bool:
        if side == "long":
            return snapshot.ema_fast < snapshot.ema_slow and snapshot.rsi < 45
        return snapshot.ema_fast > snapshot.ema_slow and snapshot.rsi > 55

    def _confidence_from_score(self, score: float, ml_result: Any) -> float:
        base = 0.45 + min(score, 6.0) * 0.05
        if ml_result:
            base = max(base, ml_result.combined_confidence)
        return min(0.95, max(0.35, base))

    def _hold(self, reason: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict[str, Any]:
        return {
            "action": "hold",
            "confidence": 0.0,
            "reason": reason,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size": None,
            "strategy_type": "eth_ai_fusion",
        }

    def _close(self, reason: str, stop_loss: float, take_profit: float) -> Dict[str, Any]:
        return {
            "action": "close",
            "confidence": 0.7,
            "reason": reason,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size": None,
            "strategy_type": "eth_ai_fusion",
        }

    def _ema(self, values: list, period: int) -> float:
        if not values:
            return 0.0
        if len(values) < period:
            return values[-1]
        k = 2 / (period + 1)
        ema = values[0]
        for price in values[1:]:
            ema = price * k + ema * (1 - k)
        return ema

    def _ema_series(self, values: list, period: int) -> list:
        if not values:
            return []
        if len(values) < period:
            return values[:]
        k = 2 / (period + 1)
        ema_values = [values[0]]
        for price in values[1:]:
            ema_values.append(price * k + ema_values[-1] * (1 - k))
        return ema_values

    def _rsi(self, closes: list, period: int) -> float:
        if len(closes) <= period:
            return 50.0
        gains = 0.0
        losses = 0.0
        for i in range(-period, 0):
            change = closes[i] - closes[i - 1]
            if change >= 0:
                gains += change
            else:
                losses += abs(change)
        if losses == 0:
            return 100.0
        rs = gains / losses
        return 100 - (100 / (1 + rs))

    def _macd_hist(self, closes: list) -> float:
        if len(closes) < 35:
            return 0.0
        ema_fast = self._ema_series(closes, 12)
        ema_slow = self._ema_series(closes, 26)
        macd_line = [f - s for f, s in zip(ema_fast[-len(ema_slow):], ema_slow)]
        signal_line = self._ema_series(macd_line, 9)
        if not signal_line:
            return 0.0
        return macd_line[-1] - signal_line[-1]

    def _atr_percent(self, highs: list, lows: list, closes: list, period: int) -> float:
        if len(closes) < period + 1:
            return 0.6
        trs = []
        for i in range(-period, 0):
            high = highs[i]
            low = lows[i]
            prev_close = closes[i - 1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        atr = sum(trs) / len(trs) if trs else 0.0
        price = closes[-1] if closes else 1.0
        if price <= 0:
            return 0.6
        return (atr / price) * 100

    def _volume_ratio(self, volumes: list, window: int) -> float:
        if not volumes:
            return 1.0
        current = volumes[-1]
        window_values = volumes[-window:] if len(volumes) >= window else volumes
        avg = sum(window_values) / len(window_values) if window_values else 0.0
        if avg == 0:
            return 1.0
        return current / avg


def create_eth_ai_fusion_strategy(
    params: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> ETHAIFusionStrategy:
    return ETHAIFusionStrategy(params=params, user_id=user_id)
