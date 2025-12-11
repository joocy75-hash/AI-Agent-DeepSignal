#!/usr/bin/env python3
"""
시장 데이터 흐름 테스트
봇이 실제로 시장 데이터를 받고 전략을 실행하는지 확인
"""

import asyncio
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.bitget_ws_collector import bitget_ws_collector

async def test_market_data_collection():
    """시장 데이터 수신 테스트"""

    # Create market queue
    market_queue = asyncio.Queue(maxsize=1000)

    print("🚀 Starting Bitget WebSocket collector...")

    # Start collector in background
    collector_task = asyncio.create_task(bitget_ws_collector(market_queue))

    # Wait and collect data
    print("⏳ Waiting for market data (30 seconds)...")

    data_count = 0
    start_time = asyncio.get_event_loop().time()
    timeout = 30  # 30 seconds

    try:
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Wait for market data with timeout
                market_data = await asyncio.wait_for(market_queue.get(), timeout=5.0)

                data_count += 1

                symbol = market_data.get('symbol', 'UNKNOWN')
                price = market_data.get('price', 0)
                timestamp = market_data.get('timestamp', 0)

                # Convert timestamp to readable time
                dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
                time_str = dt.strftime('%H:%M:%S')

                print(f"✅ [{data_count}] {time_str} - {symbol}: ${price:,.2f}")

                # Show market data structure on first receive
                if data_count == 1:
                    print(f"\n📊 Market data structure:")
                    print(json.dumps(market_data, indent=2))
                    print()

            except asyncio.TimeoutError:
                print("⚠️  No data received in last 5 seconds...")
                continue

    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")

    finally:
        # Cancel collector
        collector_task.cancel()
        try:
            await collector_task
        except asyncio.CancelledError:
            pass

    print(f"\n📈 Summary:")
    print(f"   Total data received: {data_count}")
    print(f"   Data rate: {data_count / timeout:.2f} messages/second")

    if data_count == 0:
        print("\n❌ No market data received!")
        print("   Possible issues:")
        print("   - Bitget WebSocket connection failed")
        print("   - Network connectivity issues")
        print("   - Symbol subscription issues")
    else:
        print(f"\n✅ Market data is flowing correctly!")

if __name__ == "__main__":
    asyncio.run(test_market_data_collection())
