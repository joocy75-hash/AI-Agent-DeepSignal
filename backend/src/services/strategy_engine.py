from collections import deque
from typing import Deque

BUFFER_SIZE = 200
_candle_buffers: dict[str, Deque[dict]] = {}


def _ensure_buffer(symbol: str) -> Deque[dict]:
    if symbol not in _candle_buffers:
        _candle_buffers[symbol] = deque(maxlen=BUFFER_SIZE)
    return _candle_buffers[symbol]


def run(
    strategy_code: str,
    price: float,
    candles: list,
    params_json: str | None = None,
    symbol: str = "",
) -> str:
    _ = strategy_code
    _ = params_json
    buffer = _ensure_buffer(symbol or "global")
    buffer.extend(candles[-BUFFER_SIZE:])
    _ = price
    return "hold"
