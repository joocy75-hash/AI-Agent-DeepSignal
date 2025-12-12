import requests
import sqlite3
import base64
import json
import time
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
DATABASE_PATH = "./test_db.sqlite"

# Mock Bitget REST API responses to avoid real network calls.
def mock_bitget_api(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code

        def json(self):
            return self._json_data

    # Return example mocked response data for Bitget API
    if args[0].startswith("https://api.bitget.com"):
        # Fake positions and trades data
        return MockResponse({
            "positions": [
                {"symbol": "BTCUSDT", "size": 0.5, "entryPrice": 45000, "unrealizedPNL": 100},
            ],
            "trades": [
                {"id": "trade1", "symbol": "BTCUSDT", "price": 44000, "qty": 0.5, "side": "buy", "timestamp": int(time.time()*1000)}
            ]
        })
    return MockResponse({}, 404)


def get_jwt_token(email: str, password: str) -> str:
    # Helper function to login and get auth token
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


def insert_test_portfolio_data(conn, user_id: int):
    cursor = conn.cursor()
    # Clear existing data for clean test
    cursor.execute("DELETE FROM portfolios WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM trades WHERE user_id = ?", (user_id,))
    conn.commit()

    # Insert portfolio overview
    cursor.execute(
        "INSERT INTO portfolios (user_id, asset, quantity, average_price) VALUES (?, ?, ?, ?)",
        (user_id, "BTC", 1.2, 40000.0),
    )
    # Insert some trading stats records
    cursor.execute(
        "INSERT INTO trades (user_id, symbol, quantity, price, side, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, "BTCUSDT", 0.5, 44000.0, "buy", int(time.time()) - 3600),
    )
    cursor.execute(
        "INSERT INTO trades (user_id, symbol, quantity, price, side, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, "BTCUSDT", 0.7, 46000.0, "sell", int(time.time()) - 1800),
    )
    conn.commit()


def decode_jwt_no_verify(token: str) -> dict:
    # Decode JWT token payload without verification
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT token format")
        payload_b64 = parts[1]
        # Add padding if necessary
        padding = '=' * (-len(payload_b64) % 4)
        payload_b64 += padding
        decoded_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(decoded_bytes)
        return payload
    except Exception as e:
        raise AssertionError(f"Failed to decode JWT token payload: {e}")


def test_dashboard_portfolio_and_trading_statistics_display():
    # This function tests that the dashboard endpoint returns portfolio overview, balance,
    # and trading statistics correctly reflecting the data stored in SQLite database.
    # It mocks Bitget API and uses SQLite for backend data validation.

    # Credentials for login - this should be a test user set up in the test environment
    test_email = "testuser@example.com"
    test_password = "TestPassword123"

    # Step 1: Get JWT auth token
    token = get_jwt_token(test_email, test_password)
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Setup SQLite test database connection
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Identify user_id from JWT token for the test user
        decoded = decode_jwt_no_verify(token)
        user_id = decoded.get("sub")
        assert user_id is not None

        # Step 3: Insert test portfolio and trades data for the user to validate dashboard
        insert_test_portfolio_data(conn, user_id)

        with mock.patch("requests.get", side_effect=mock_bitget_api):
            # Step 4: Request dashboard data from backend
            resp = requests.get(f"{BASE_URL}/api/dashboard", headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            dashboard_data = resp.json()

            # Step 5: Validate portfolio overview
            portfolio = dashboard_data.get("portfolio_overview")
            assert portfolio is not None, "Portfolio overview is missing"
            btc_holding = next((p for p in portfolio if p["asset"] == "BTC"), None)
            assert btc_holding is not None, "BTC holding not found in portfolio overview"
            assert abs(btc_holding["quantity"] - 1.2) < 0.0001, "BTC quantity mismatch"

            # Step 6: Validate balance info
            balance = dashboard_data.get("balance")
            assert balance is not None, "Balance data is missing"
            assert isinstance(balance.get("total"), (int, float)), "Total balance must be numeric"

            # Step 7: Validate trading statistics
            trading_stats = dashboard_data.get("trading_statistics")
            assert trading_stats is not None, "Trading statistics missing"
            # Check example stats keys (total trades, profit/loss, etc)
            assert "total_trades" in trading_stats
            assert "profit_loss" in trading_stats

            # Additional validation: trading stats total_trades should reflect DB
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades WHERE user_id = ?", (user_id,))
            trade_count_db = cursor.fetchone()[0]
            assert trading_stats["total_trades"] == trade_count_db, "Total trades count mismatch"

    finally:
        conn.close()


test_dashboard_portfolio_and_trading_statistics_display()
