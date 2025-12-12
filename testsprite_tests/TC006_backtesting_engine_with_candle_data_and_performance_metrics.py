import requests
import sqlite3
import json
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Mock data for candle data used in backtesting
MOCK_CANDLE_DATA = [
    {"timestamp": 1672502400, "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
    {"timestamp": 1672506000, "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1200},
    {"timestamp": 1672509600, "open": 110, "high": 120, "low": 100, "close": 115, "volume": 900},
    {"timestamp": 1672513200, "open": 115, "high": 125, "low": 105, "close": 120, "volume": 1300},
]


def test_backtesting_engine_with_candle_data_and_performance_metrics():
    # Setup in-memory SQLite database for testing
    conn = sqlite3.connect(":memory:")
    try:
        # Create tables as expected by backtesting service (example schema)
        conn.execute("""
        CREATE TABLE candle_data (
            timestamp INTEGER PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
        )""")
        conn.execute("""
        CREATE TABLE bot_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            strategy_config TEXT
        )""")
        conn.commit()

        # Insert mock candle data into candle_data table
        for candle in MOCK_CANDLE_DATA:
            conn.execute(
                "INSERT INTO candle_data (timestamp, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?)",
                (candle['timestamp'], candle['open'], candle['high'], candle['low'], candle['close'], candle['volume'])
            )
        conn.commit()

        # Mock authentication token retrieval (assuming JWT token needed)
        # For this test assume a token is available or use a dummy token for Authorization header
        auth_token = "Bearer dummy-jwt-token"

        headers = {"Authorization": auth_token, "Content-Type": "application/json"}

        # Create a grid trading bot (mocked)
        bot_payload = {
            "name": "Test Grid Bot",
            "strategy_type": "grid",
            "config": {
                "grid_spacing": 0.01,
                "grid_levels": 5,
                "base_order_size": 1.0
            }
        }

        # Use try-finally to ensure bot is deleted after test
        create_bot_resp = requests.post(
            f"{BASE_URL}/api/bot_instances",
            headers=headers,
            json=bot_payload,
            timeout=TIMEOUT
        )
        assert create_bot_resp.status_code == 201, f"Bot creation failed: {create_bot_resp.text}"
        bot_data = create_bot_resp.json()
        bot_id = bot_data.get("id")
        assert bot_id is not None, "Bot ID not returned on creation"

        # Mock the external Bitget API calls to avoid real network calls
        # We patch requests.post/requests.get method used by backtesting internally
        # Here we assume the backtest endpoint does not call real APIs directly in this test context

        # Prepare backtest request payload with historical candle timestamps and bot id
        backtest_payload = {
            "bot_id": bot_id,
            "start_timestamp": MOCK_CANDLE_DATA[0]['timestamp'],
            "end_timestamp": MOCK_CANDLE_DATA[-1]['timestamp']
        }

        # Call backtest endpoint
        backtest_resp = requests.post(
            f"{BASE_URL}/api/backtest/grid",
            headers=headers,
            json=backtest_payload,
            timeout=TIMEOUT
        )
        assert backtest_resp.status_code == 200, f"Backtest API call failed: {backtest_resp.text}"

        backtest_result = backtest_resp.json()

        # Validate returned performance metrics exist and are reasonable
        expected_metrics = ["total_return", "max_drawdown", "win_rate", "number_of_trades", "net_profit"]
        for metric in expected_metrics:
            assert metric in backtest_result, f"Performance metric '{metric}' missing in backtest result"
            # Assert metric values are numbers and sane
            val = backtest_result[metric]
            assert isinstance(val, (int, float)), f"Metric {metric} value is not numeric"
            if metric in ["total_return", "net_profit"]:
                # These can be positive or negative
                assert val != 0, f"Metric {metric} should not be zero for test data"
            elif metric == "win_rate":
                assert 0.0 <= val <= 1.0, f"Win rate {val} not between 0 and 1"
            elif metric == "max_drawdown":
                assert val >= 0, f"Max drawdown {val} should be non-negative"
            elif metric == "number_of_trades":
                assert val >= 0 and isinstance(val, int), f"Number_of_trades {val} invalid"

        # Test position closing logic by querying backtesting details
        # Example: examine trades from backtest_result if present
        trades = backtest_result.get("trades", [])
        assert isinstance(trades, list), "Trades field should be a list"
        # Check at least one trade is closed properly (closing price exists)
        trade_closed_correctly = any("close_price" in t and t["close_price"] is not None for t in trades)
        assert trade_closed_correctly, "No properly closed positions found in backtest trades"

    finally:
        # Clean up: delete created bot instance if it was created
        if 'bot_id' in locals():
            try:
                del_resp = requests.delete(
                    f"{BASE_URL}/api/bot_instances/{bot_id}",
                    headers=headers,
                    timeout=TIMEOUT
                )
                assert del_resp.status_code in (200, 204), f"Failed to delete bot: {del_resp.text}"
            except Exception:
                pass
        conn.close()


test_backtesting_engine_with_candle_data_and_performance_metrics()
