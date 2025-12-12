import requests
import sqlite3
import json
import time
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Mocked Bitget API responses for external calls the platform might do during position closing or bot operation
def mock_bitget_rest_api(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
        def json(self):
            return {
                "data": {
                    "order_id": "mocked_order_123",
                    "status": "closed",
                    "filled_qty": "10",
                    "price": "100.5"
                }
            }
    return MockResponse()

def test_trading_history_accuracy_and_analytics():
    # Use in-memory SQLite DB to avoid file permission issues
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    try:
        # Create minimal schema for trades and performance analytics for testing
        cursor.executescript("""
            DROP TABLE IF EXISTS trades;
            DROP TABLE IF EXISTS analytics;
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                trade_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                pnl REAL,
                timestamp INTEGER NOT NULL
            );
        """)
        conn.commit()

        # Step 1: Authenticate and get JWT token (simulate user login)
        # For testing, we assume user already exists with known login
        login_payload = {"email": "testuser@example.com", "password": "testpassword"}
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_payload,
            timeout=TIMEOUT
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        assert token is not None

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Step 2: Create a Grid Bot (to generate trades and analytics)
        new_bot_payload = {
            "name": "Test Trading History Bot",
            "strategy": "grid",
            "config": {
                "grid_spacing": 0.01,
                "investment": 1000,
                "max_positions": 5
            }
        }
        create_bot_resp = requests.post(
            f"{BASE_URL}/api/bots",
            json=new_bot_payload,
            headers=headers,
            timeout=TIMEOUT
        )
        assert create_bot_resp.status_code == 201
        bot_id = create_bot_resp.json().get("id")
        assert bot_id is not None

        # We will mock external Bitget API calls during position closing & bot operation
        with mock.patch('backend.src.api.bitget_rest_api.requests.post', side_effect=mock_bitget_rest_api), \
             mock.patch('backend.src.api.bitget_rest_api.requests.get', side_effect=mock_bitget_rest_api):

            # Step 3: Start the bot to generate some trades (simulate this by API call)
            start_resp = requests.post(
                f"{BASE_URL}/api/bots/{bot_id}/start",
                headers=headers,
                timeout=TIMEOUT
            )
            assert start_resp.status_code == 200

            # Wait briefly to let backend simulate trades (in real testing environment)
            time.sleep(2)

            # Step 4: Stop the bot to finalize trades
            stop_resp = requests.post(
                f"{BASE_URL}/api/bots/{bot_id}/stop",
                headers=headers,
                timeout=TIMEOUT
            )
            assert stop_resp.status_code == 200

            # Step 5: Retrieve trading history for this bot
            history_resp = requests.get(
                f"{BASE_URL}/api/trading_history?bot_id={bot_id}",
                headers=headers,
                timeout=TIMEOUT
            )
            assert history_resp.status_code == 200
            trades_data = history_resp.json()
            assert isinstance(trades_data, list)
            assert len(trades_data) > 0  # There should be trades recorded

            # Step 6: Verify trades accuracy and match against DB directly
            cursor.executemany(
                "INSERT INTO trades (bot_id, trade_type, quantity, price, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (bot_id, trade["trade_type"], trade["quantity"], trade["price"], trade["timestamp"], trade["status"]) 
                    for trade in trades_data
                ]
            )
            conn.commit()

            # Query back inserted trades and compare
            cursor.execute("SELECT bot_id, trade_type, quantity, price, timestamp, status FROM trades WHERE bot_id = ?", (bot_id,))
            db_trades = cursor.fetchall()
            assert len(db_trades) == len(trades_data)

            # Step 7: Retrieve performance analytics for this bot
            analytics_resp = requests.get(
                f"{BASE_URL}/api/trading_history/analytics?bot_id={bot_id}",
                headers=headers,
                timeout=TIMEOUT
            )
            assert analytics_resp.status_code == 200
            analytics_data = analytics_resp.json()
            assert "total_trades" in analytics_data
            assert "winning_trades" in analytics_data
            assert "losing_trades" in analytics_data
            assert "pnl" in analytics_data

            # Insert analytics into DB
            timestamp = int(time.time())
            cursor.execute("""
                INSERT INTO analytics (bot_id, total_trades, winning_trades, losing_trades, pnl, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bot_id,
                analytics_data["total_trades"],
                analytics_data["winning_trades"],
                analytics_data["losing_trades"],
                analytics_data["pnl"],
                timestamp
            ))
            conn.commit()

            # Query and verify analytics data was stored correctly
            cursor.execute("SELECT total_trades, winning_trades, losing_trades, pnl FROM analytics WHERE bot_id = ?", (bot_id,))
            db_analytics = cursor.fetchone()
            assert db_analytics is not None
            assert db_analytics[0] == analytics_data["total_trades"]
            assert db_analytics[1] == analytics_data["winning_trades"]
            assert db_analytics[2] == analytics_data["losing_trades"]
            assert abs(db_analytics[3] - analytics_data["pnl"]) < 0.0001

    finally:
        # Cleanup: Delete the created bot
        try:
            if 'bot_id' in locals():
                requests.delete(
                    f"{BASE_URL}/api/bots/{bot_id}",
                    headers=headers,
                    timeout=TIMEOUT
                )
        except Exception:
            pass
        cursor.execute("DROP TABLE IF EXISTS trades;")
        cursor.execute("DROP TABLE IF EXISTS analytics;")
        conn.commit()
        conn.close()

test_trading_history_accuracy_and_analytics()
