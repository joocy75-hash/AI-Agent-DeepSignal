"""
백테스트 스크립트

기존 전략을 백테스팅하거나 새 전략을 테스트할 때 사용합니다.

사용법:
    python backtest_script.py --strategy balanced --symbol BTCUSDT --start 2024-01-01 --end 2024-06-01
"""

import argparse
import asyncio
import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 프로젝트 경로 설정 (필요시 수정)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_INITIAL_BALANCE = 10000.0
DEFAULT_FEE_RATE = 0.0006  # 0.06%
DEFAULT_SLIPPAGE = 0.0001  # 0.01%

STRATEGY_PARAMS = {
    "aggressive": {
        "rsi_period": 14,
        "rsi_oversold": 25,
        "rsi_overbought": 75,
        "stop_loss_percent": 1.5,
        "take_profit_percent": 4.0,
        "position_size_percent": 40,
        "leverage": 10,
    },
    "balanced": {
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 4.0,
        "position_size_percent": 30,
        "leverage": 5,
    },
    "conservative": {
        "rsi_period": 14,
        "rsi_oversold": 35,
        "rsi_overbought": 65,
        "stop_loss_percent": 3.0,
        "take_profit_percent": 4.5,
        "position_size_percent": 20,
        "leverage": 3,
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 캔들 데이터 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def load_candles_from_csv(csv_path: str) -> list:
    """CSV에서 캔들 데이터 로드"""
    candles = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "timestamp": row["timestamp"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })

    return candles


async def fetch_candles_from_api(
    symbol: str,
    interval: str,
    start_date: str,
    end_date: str,
) -> list:
    """
    Bitget API에서 캔들 데이터 가져오기

    Note: API 키 없이 public API 사용
    """
    try:
        from src.services.bitget_rest import BitgetRestClient

        client = BitgetRestClient()  # 인증 없이 생성

        candles = await client.get_all_historical_candles(
            symbol=symbol,
            interval=interval,
            start_time=start_date,
            end_time=end_date,
        )

        await client.close()
        return candles

    except ImportError:
        print("Warning: bitget_rest 모듈을 찾을 수 없습니다. CSV 파일을 사용하세요.")
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 백테스트 엔진 (간단 버전)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def calculate_rsi(closes: list, period: int = 14) -> list:
    """RSI 계산"""
    if len(closes) < period + 1:
        return []

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


class SimpleBacktest:
    """간단한 백테스트 엔진"""

    def __init__(
        self,
        initial_balance: float = DEFAULT_INITIAL_BALANCE,
        fee_rate: float = DEFAULT_FEE_RATE,
        slippage: float = DEFAULT_SLIPPAGE,
    ):
        self.initial_balance = initial_balance
        self.fee_rate = fee_rate
        self.slippage = slippage

    def run(self, candles: list, params: dict) -> dict:
        """백테스트 실행"""
        balance = self.initial_balance
        position = None
        trades = []
        equity_curve = []

        closes = [c["close"] for c in candles]

        for i, candle in enumerate(candles):
            # RSI 계산 (충분한 데이터가 필요)
            if i < params.get("rsi_period", 14) + 10:
                equity_curve.append(balance)
                continue

            rsi_values = calculate_rsi(closes[: i + 1], params.get("rsi_period", 14))
            if not rsi_values:
                equity_curve.append(balance if position is None else balance + self._calc_unrealized(position, candle["close"]))
                continue

            current_rsi = rsi_values[-1]
            price = candle["close"]

            # 포지션 없을 때 - 진입 시그널 확인
            if position is None:
                # 롱 진입
                if current_rsi < params.get("rsi_oversold", 30):
                    entry_price = price * (1 + self.slippage)
                    fee = entry_price * self.fee_rate
                    balance -= fee
                    position = {
                        "side": "LONG",
                        "entry_price": entry_price,
                        "entry_fee": fee,
                        "timestamp": candle["timestamp"],
                    }
                # 숏 진입
                elif current_rsi > params.get("rsi_overbought", 70):
                    entry_price = price * (1 - self.slippage)
                    fee = entry_price * self.fee_rate
                    balance -= fee
                    position = {
                        "side": "SHORT",
                        "entry_price": entry_price,
                        "entry_fee": fee,
                        "timestamp": candle["timestamp"],
                    }

            # 포지션 있을 때 - 청산 조건 확인
            else:
                should_close = False
                exit_price = price
                exit_reason = ""

                entry_price = position["entry_price"]
                sl_percent = params.get("stop_loss_percent", 2.0) / 100
                tp_percent = params.get("take_profit_percent", 4.0) / 100

                if position["side"] == "LONG":
                    sl_price = entry_price * (1 - sl_percent)
                    tp_price = entry_price * (1 + tp_percent)

                    if price <= sl_price:
                        should_close = True
                        exit_price = price * (1 - self.slippage)
                        exit_reason = "stop_loss"
                    elif price >= tp_price:
                        should_close = True
                        exit_price = price * (1 - self.slippage)
                        exit_reason = "take_profit"
                    elif current_rsi > params.get("rsi_overbought", 70):
                        should_close = True
                        exit_price = price * (1 - self.slippage)
                        exit_reason = "signal_reverse"

                else:  # SHORT
                    sl_price = entry_price * (1 + sl_percent)
                    tp_price = entry_price * (1 - tp_percent)

                    if price >= sl_price:
                        should_close = True
                        exit_price = price * (1 + self.slippage)
                        exit_reason = "stop_loss"
                    elif price <= tp_price:
                        should_close = True
                        exit_price = price * (1 + self.slippage)
                        exit_reason = "take_profit"
                    elif current_rsi < params.get("rsi_oversold", 30):
                        should_close = True
                        exit_price = price * (1 + self.slippage)
                        exit_reason = "signal_reverse"

                if should_close:
                    # PnL 계산
                    if position["side"] == "LONG":
                        pnl = exit_price - entry_price
                    else:
                        pnl = entry_price - exit_price

                    exit_fee = exit_price * self.fee_rate
                    balance += pnl - exit_fee

                    trades.append({
                        "side": position["side"],
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": pnl - position["entry_fee"] - exit_fee,
                        "pnl_percent": ((exit_price / entry_price) - 1) * 100 if position["side"] == "LONG" else ((entry_price / exit_price) - 1) * 100,
                        "exit_reason": exit_reason,
                        "entry_time": position["timestamp"],
                        "exit_time": candle["timestamp"],
                    })

                    position = None

            # Equity 기록
            if position is None:
                equity_curve.append(balance)
            else:
                unrealized = self._calc_unrealized(position, price)
                equity_curve.append(balance + unrealized)

        # 마지막에 포지션이 열려있으면 청산
        if position is not None:
            price = candles[-1]["close"]
            if position["side"] == "LONG":
                exit_price = price * (1 - self.slippage)
                pnl = exit_price - position["entry_price"]
            else:
                exit_price = price * (1 + self.slippage)
                pnl = position["entry_price"] - exit_price

            exit_fee = exit_price * self.fee_rate
            balance += pnl - exit_fee

            trades.append({
                "side": position["side"],
                "entry_price": position["entry_price"],
                "exit_price": exit_price,
                "pnl": pnl - position["entry_fee"] - exit_fee,
                "exit_reason": "end_of_period",
            })

        # 메트릭스 계산
        metrics = self._calculate_metrics(trades, equity_curve)

        return {
            "initial_balance": self.initial_balance,
            "final_balance": balance,
            "trades": trades,
            "equity_curve": equity_curve,
            "metrics": metrics,
        }

    def _calc_unrealized(self, position: dict, current_price: float) -> float:
        """미실현 손익 계산"""
        if position["side"] == "LONG":
            return current_price - position["entry_price"]
        else:
            return position["entry_price"] - current_price

    def _calculate_metrics(self, trades: list, equity_curve: list) -> dict:
        """성과 메트릭스 계산"""
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_return": 0,
                "max_drawdown": 0,
            }

        # 승률
        wins = sum(1 for t in trades if t["pnl"] > 0)
        win_rate = (wins / len(trades)) * 100

        # 수익률
        total_return = ((equity_curve[-1] / self.initial_balance) - 1) * 100

        # 최대 낙폭
        peak = equity_curve[0]
        max_drawdown = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # 평균 손익
        avg_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0) / wins if wins > 0 else 0
        losses = sum(1 for t in trades if t["pnl"] < 0)
        avg_loss = sum(t["pnl"] for t in trades if t["pnl"] < 0) / losses if losses > 0 else 0

        return {
            "total_trades": len(trades),
            "winning_trades": wins,
            "losing_trades": losses,
            "win_rate": round(win_rate, 2),
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "avg_profit": round(avg_profit, 4),
            "avg_loss": round(avg_loss, 4),
            "profit_factor": round(abs(avg_profit / avg_loss), 2) if avg_loss != 0 else 0,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def main():
    parser = argparse.ArgumentParser(description="백테스트 스크립트")
    parser.add_argument("--strategy", type=str, default="balanced", choices=["aggressive", "balanced", "conservative"])
    parser.add_argument("--symbol", type=str, default="BTCUSDT")
    parser.add_argument("--interval", type=str, default="1h")
    parser.add_argument("--start", type=str, required=True, help="시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="종료일 (YYYY-MM-DD)")
    parser.add_argument("--csv", type=str, help="CSV 파일 경로 (API 대신 사용)")
    parser.add_argument("--initial-balance", type=float, default=DEFAULT_INITIAL_BALANCE)
    parser.add_argument("--output", type=str, help="결과 JSON 파일 경로")

    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"백테스트 실행: {args.strategy} 전략")
    print(f"심볼: {args.symbol}, 기간: {args.start} ~ {args.end}")
    print(f"{'=' * 60}\n")

    # 캔들 데이터 로드
    if args.csv:
        print(f"CSV 파일에서 데이터 로드: {args.csv}")
        candles = load_candles_from_csv(args.csv)
    else:
        print(f"API에서 데이터 가져오는 중...")
        candles = await fetch_candles_from_api(args.symbol, args.interval, args.start, args.end)

    if not candles:
        print("Error: 캔들 데이터를 로드할 수 없습니다.")
        return

    print(f"로드된 캔들 수: {len(candles)}")

    # 백테스트 실행
    params = STRATEGY_PARAMS[args.strategy]
    backtest = SimpleBacktest(initial_balance=args.initial_balance)

    print("\n백테스트 실행 중...")
    result = backtest.run(candles, params)

    # 결과 출력
    print(f"\n{'=' * 60}")
    print("백테스트 결과")
    print(f"{'=' * 60}")
    print(f"초기 잔고: ${result['initial_balance']:,.2f}")
    print(f"최종 잔고: ${result['final_balance']:,.2f}")
    print(f"총 수익률: {result['metrics']['total_return']}%")
    print(f"최대 낙폭: {result['metrics']['max_drawdown']}%")
    print(f"총 거래 수: {result['metrics']['total_trades']}")
    print(f"승률: {result['metrics']['win_rate']}%")
    print(f"손익비: {result['metrics']['profit_factor']}")
    print(f"{'=' * 60}\n")

    # JSON 저장
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"결과가 저장되었습니다: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
