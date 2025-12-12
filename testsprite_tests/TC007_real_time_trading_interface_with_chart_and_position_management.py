import requests
import sqlite3
import json
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

# Mocking Bitget API calls inside the tested backend service (assuming endpoint calls it)
# We will mock requests.post/get used for Bitget API within the backend if such calls are proxied through /external/bitget or similar.
# Here, we simulate mocking at the requests level for simplicity.

def mock_bitget_api(*args, **kwargs):
    # Sample mock response for Bitget API calls
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self._json = {
                "success": True,
                "data": {
                    "positionId": "mock-position-id",
                    "status": "closed"
                }
            }
        def json(self):
            return self._json
    return MockResponse()

def test_real_time_trading_interface_with_chart_and_position_management():
    # Setup SQLite connection (in-memory for test isolation)
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    try:
        # Assuming DB schema involves tables: users, bots, positions
        cursor.executescript("""
        CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT);
        CREATE TABLE bots(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, bot_type TEXT, config TEXT, status TEXT);
        CREATE TABLE positions(id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER, symbol TEXT, side TEXT, qty REAL, status TEXT);
        """)
        conn.commit()

        # 1. Create a test user (simulate signup)
        test_email = "testuser@example.com"
        test_password = "securepassword"
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (test_email, test_password))
        user_id = cursor.lastrowid
        conn.commit()

        # 2. Mock authentication to get token (simulate login)
        auth_payload = {"email": test_email, "password": test_password}
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=auth_payload, timeout=TIMEOUT)
        login_resp.raise_for_status()
        auth_token = login_resp.json().get("access_token")
        assert auth_token, "No access token received"

        auth_headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

        # 3. Create a bot (bot creation flow)
        bot_create_payload = {
            "bot_type": "grid",
            "config": {
                "symbol": "BTCUSDT",
                "grid_size": 10,
                "investment": 1000
            }
        }
        bot_resp = requests.post(f"{BASE_URL}/api/bots", headers=auth_headers, json=bot_create_payload, timeout=TIMEOUT)
        bot_resp.raise_for_status()
        bot = bot_resp.json()
        bot_id = bot.get("id")
        assert bot_id, "Bot creation failed, no ID returned"

        # 4. Start the bot
        start_resp = requests.post(f"{BASE_URL}/api/bots/{bot_id}/start", headers=auth_headers, timeout=TIMEOUT)
        start_resp.raise_for_status()
        assert start_resp.json().get("status") == "running"

        # 5. Open a position using the bot - note: Position opening API assumed as /api/positions with bot_id
        position_payload = {
            "bot_id": bot_id,
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": 0.1
        }

        # Patch requests.post inside this scope to mock Bitget API calls the backend would make internally
        with mock.patch("requests.post", side_effect=mock_bitget_api):
            pos_resp = requests.post(f"{BASE_URL}/api/positions", headers=auth_headers, json=position_payload, timeout=TIMEOUT)
            pos_resp.raise_for_status()
            position = pos_resp.json()
            position_id = position.get("id")
            assert position_id, "Position opening failed, no position ID returned"
            assert position.get("status") == "open"

            # 6. Fetch live TradingView chart data (simulated via endpoint /api/trading/chart)
            chart_resp = requests.get(f"{BASE_URL}/api/trading/chart?symbol=BTCUSDT", headers=auth_headers, timeout=TIMEOUT)
            chart_resp.raise_for_status()
            chart_data = chart_resp.json()
            assert "candles" in chart_data and isinstance(chart_data["candles"], list)

            # 7. Close the position to test position closing logic
            close_resp = requests.post(f"{BASE_URL}/api/positions/{position_id}/close", headers=auth_headers, timeout=TIMEOUT)
            close_resp.raise_for_status()
            close_data = close_resp.json()
            assert close_data.get("status") == "closed", "Position closing status is not closed"

        # 8. Stop and delete the bot (cleanup)
        stop_resp = requests.post(f"{BASE_URL}/api/bots/{bot_id}/stop", headers=auth_headers, timeout=TIMEOUT)
        stop_resp.raise_for_status()
        assert stop_resp.json().get("status") == "stopped"

        del_resp = requests.delete(f"{BASE_URL}/api/bots/{bot_id}", headers=auth_headers, timeout=TIMEOUT)
        del_resp.raise_for_status()
        assert del_resp.status_code == 204

    finally:
        # Cleanup DB connection
        conn.close()

test_real_time_trading_interface_with_chart_and_position_management()
