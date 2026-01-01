from typing import List

from .base import StrategyBase


class EthAIFusionBacktestStrategy(StrategyBase):
    def __init__(self):
        self._candles: List[dict] = []
        self._ema_fast = 9
        self._ema_slow = 21
        self._rsi_length = 14
        self._atr_length = 14

    def on_candle(self, candle: dict, position: dict | None) -> str:
        self._candles.append(candle)
        if len(self._candles) < 60:
            return "hold"

        closes = [c.get("close", 0) for c in self._candles]
        highs = [c.get("high", 0) for c in self._candles]
        lows = [c.get("low", 0) for c in self._candles]

        ema_fast = self._ema(closes, self._ema_fast)
        ema_slow = self._ema(closes, self._ema_slow)
        rsi = self._rsi(closes, self._rsi_length)
        atr_percent = self._atr_percent(highs, lows, closes, self._atr_length)
        stop_loss = max(0.6, min(1.6, atr_percent * 1.2))
        take_profit = max(1.2, min(4.5, atr_percent * 2.4))

        if position:
            side = position.get("direction", "long")
            entry = float(position.get("entry_price", closes[-1]))
            pnl_percent = self._pnl_percent(side, entry, closes[-1])
            if pnl_percent <= -stop_loss or pnl_percent >= take_profit:
                return "sell" if side == "long" else "buy"
            if side == "long" and ema_fast < ema_slow and rsi < 45:
                return "sell"
            if side == "short" and ema_fast > ema_slow and rsi > 55:
                return "buy"

        if ema_fast > ema_slow and rsi >= 50:
            return "buy"
        if ema_fast < ema_slow and rsi <= 50:
            return "sell"
        return "hold"

    def _pnl_percent(self, side: str, entry_price: float, current_price: float) -> float:
        if entry_price <= 0:
            return 0.0
        if side == "long":
            return ((current_price - entry_price) / entry_price) * 100
        return ((entry_price - current_price) / entry_price) * 100

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
