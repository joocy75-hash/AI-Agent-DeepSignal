"""
실전거래 테스트용 AI 전략 백테스트 스크립트

사용법:
    python3 test_strategy_backtest.py
"""

import json
from datetime import datetime
from src.strategies.test_live_strategy import create_test_strategy


def generate_sample_candles(num_candles=100):
    """샘플 캔들 데이터 생성 (실제로는 거래소 API에서 가져와야 함)"""
    import random

    candles = []
    base_price = 50000.0
    current_price = base_price

    for i in range(num_candles):
        # 랜덤 가격 변동 (-2% ~ +2%)
        change_pct = random.uniform(-0.02, 0.02)
        current_price = current_price * (1 + change_pct)

        open_price = current_price
        close_price = current_price * (1 + random.uniform(-0.01, 0.01))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
        volume = random.uniform(100, 1000)

        candle = {
            "time": i,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        }
        candles.append(candle)

    return candles


def run_backtest():
    """백테스트 실행"""

    print("\n" + "="*60)
    print("실전거래 테스트용 AI 전략 백테스트")
    print("="*60 + "\n")

    # 1. 전략 생성
    strategy = create_test_strategy()

    # 2. 샘플 데이터 생성 (실제로는 거래소 데이터 사용)
    print("📊 샘플 데이터 생성 중...")
    candles = generate_sample_candles(200)
    print(f"   생성된 캔들 수: {len(candles)}\n")

    # 3. 백테스트 실행
    print("🔄 백테스트 실행 중...\n")

    trades = []
    current_position = None
    balance = 10000.0  # 초기 자금 $10,000
    initial_balance = balance

    for i, candle in enumerate(candles):
        current_price = candle["close"]

        # 시그널 생성
        signal = strategy.generate_signal(
            current_price=current_price,
            candles=candles[:i+1],
            current_position=current_position
        )

        # 시그널 처리
        if signal["action"] == "buy" and current_position is None:
            # 매수
            position_size = signal["size"]
            cost = current_price * position_size
            if cost <= balance:
                current_position = {
                    "side": "long",
                    "entry_price": current_price,
                    "size": position_size,
                    "entry_time": i,
                    "stop_loss": signal["stop_loss"],
                    "take_profit": signal["take_profit"]
                }
                balance -= cost
                print(f"[{i:3d}] 🟢 BUY  | Price: ${current_price:,.2f} | Size: {position_size} | Confidence: {signal['confidence']:.2f}")
                print(f"       Reason: {signal['reason']}")
                print(f"       Stop Loss: ${signal['stop_loss']:,.2f} | Take Profit: ${signal['take_profit']:,.2f}\n")

        elif signal["action"] == "sell" and current_position is None:
            # 매도 (숏)
            position_size = signal["size"]
            current_position = {
                "side": "short",
                "entry_price": current_price,
                "size": position_size,
                "entry_time": i,
                "stop_loss": signal["stop_loss"],
                "take_profit": signal["take_profit"]
            }
            print(f"[{i:3d}] 🔴 SELL | Price: ${current_price:,.2f} | Size: {position_size} | Confidence: {signal['confidence']:.2f}")
            print(f"       Reason: {signal['reason']}")
            print(f"       Stop Loss: ${signal['stop_loss']:,.2f} | Take Profit: ${signal['take_profit']:,.2f}\n")

        elif signal["action"] == "close" and current_position is not None:
            # 포지션 청산
            entry_price = current_position["entry_price"]
            position_size = current_position["size"]
            side = current_position["side"]

            if side == "long":
                pnl = (current_price - entry_price) * position_size
                balance += (entry_price * position_size) + pnl
            else:  # short
                pnl = (entry_price - current_price) * position_size
                balance += pnl

            pnl_pct = (pnl / (entry_price * position_size)) * 100

            trade_record = {
                "entry_time": current_position["entry_time"],
                "exit_time": i,
                "side": side,
                "entry_price": entry_price,
                "exit_price": current_price,
                "size": position_size,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exit_reason": signal["reason"]
            }
            trades.append(trade_record)

            pnl_emoji = "✅" if pnl > 0 else "❌"
            print(f"[{i:3d}] {pnl_emoji} CLOSE | Price: ${current_price:,.2f} | PnL: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
            print(f"       Reason: {signal['reason']}")
            print(f"       Duration: {i - current_position['entry_time']} candles\n")

            current_position = None

    # 4. 결과 요약
    print("\n" + "="*60)
    print("백테스트 결과 요약")
    print("="*60 + "\n")

    total_trades = len(trades)
    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] <= 0]

    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(t["pnl"] for t in trades)
    avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    final_balance = balance
    roi = ((final_balance - initial_balance) / initial_balance) * 100

    print(f"📊 총 거래 횟수: {total_trades}")
    print(f"✅ 승리 거래: {len(winning_trades)}")
    print(f"❌ 손실 거래: {len(losing_trades)}")
    print(f"📈 승률: {win_rate:.2f}%")
    print(f"\n💰 초기 자금: ${initial_balance:,.2f}")
    print(f"💰 최종 자금: ${final_balance:,.2f}")
    print(f"{'📈' if total_pnl > 0 else '📉'} 총 손익: ${total_pnl:,.2f} ({roi:+.2f}%)")
    print(f"\n💵 평균 수익: ${avg_win:,.2f}")
    print(f"💸 평균 손실: ${avg_loss:,.2f}")

    if avg_loss != 0:
        profit_factor = abs(avg_win / avg_loss)
        print(f"📊 Profit Factor: {profit_factor:.2f}")

    print("\n" + "="*60)
    print("상세 거래 내역")
    print("="*60 + "\n")

    for i, trade in enumerate(trades, 1):
        pnl_emoji = "✅" if trade["pnl"] > 0 else "❌"
        print(f"{i}. {pnl_emoji} {trade['side'].upper()}")
        print(f"   진입: ${trade['entry_price']:,.2f} (캔들 {trade['entry_time']})")
        print(f"   청산: ${trade['exit_price']:,.2f} (캔들 {trade['exit_time']})")
        print(f"   손익: ${trade['pnl']:,.2f} ({trade['pnl_pct']:+.2f}%)")
        print(f"   사유: {trade['exit_reason']}\n")

    print("\n⚠️  주의: 이것은 샘플 데이터를 사용한 시뮬레이션입니다.")
    print("실제 백테스트는 거래소의 실제 과거 데이터를 사용해야 합니다.\n")


if __name__ == "__main__":
    run_backtest()
