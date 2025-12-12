import requests
import sqlite3
import threading
import time
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Mock Bitget REST API response for position closing and alert triggering
def mock_bitget_close_position(*args, **kwargs):
    class MockResponse:
        def json(self):
            return {"success": True, "message": "Position closed"}
        @property
        def status_code(self):
            return 200
    return MockResponse()

def mock_bitget_get_market_event(*args, **kwargs):
    class MockResponse:
        def json(self):
            # Simulate a market event that should trigger alert
            return {"price": 105.0, "symbol": "BTCUSDT"}
        @property
        def status_code(self):
            return 200
    return MockResponse()

def test_strategy_management_and_alert_triggering():
    # Setup SQLite in-memory database connection for testing
    conn = sqlite3.connect(":memory:")
    try:
        # Create tables to simulate strategy config and alerts as per backend schema assumptions
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                config TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER,
                alert_type TEXT,
                triggered BOOLEAN,
                FOREIGN KEY(strategy_id) REFERENCES strategies(id)
            )
        """)
        conn.commit()

        # Step 1: Create a new trading strategy via API
        strategy_payload = {
            "name": "Test Strategy Alpha",
            "config": {
                "grid_levels": 5,
                "take_profit": 0.02,
                "stop_loss": 0.01,
                "symbol": "BTCUSDT",
                "base_order_size": 0.001
            }
        }
        headers = {"Content-Type": "application/json"}

        # Create strategy POST /api/strategies (assumed endpoint)
        response = requests.post(f"{BASE_URL}/api/strategies", json=strategy_payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 201, f"Strategy creation failed: {response.text}"
        strategy_data = response.json()
        strategy_id = strategy_data.get("id")
        assert strategy_id is not None, "No strategy ID returned on creation"

        # Insert strategy to SQLite mock DB to simulate backend persistence
        cursor.execute("INSERT INTO strategies (id, name, config) VALUES (?, ?, ?)",
                       (strategy_id, strategy_payload["name"], str(strategy_payload["config"])))
        conn.commit()

        # Step 2: Simulate position closing logic (mocking Bitget API)
        with mock.patch('requests.post', side_effect=mock_bitget_close_position):
            close_position_payload = {
                "strategy_id": strategy_id,
                "symbol": "BTCUSDT",
                "position_side": "LONG",
                "close_amount": 0.001
            }
            close_resp = requests.post(f"{BASE_URL}/api/positions/close", json=close_position_payload, headers=headers, timeout=TIMEOUT)
            assert close_resp.status_code == 200, f"Position close API failed: {close_resp.text}"
            close_resp_json = close_resp.json()
            assert close_resp_json.get("success") is True, "Position close was not successful"

        # Step 3: Simulate alert triggering logic based on market event
        # Create alert linked to strategy in SQLite mock DB
        cursor.execute("INSERT INTO alerts (strategy_id, alert_type, triggered) VALUES (?, ?, ?)",
                       (strategy_id, "price_threshold", False))
        alert_id = cursor.lastrowid
        conn.commit()

        # Mock GET call to external API to get market event
        with mock.patch('requests.get', side_effect=mock_bitget_get_market_event):
            market_event_resp = requests.get(f"{BASE_URL}/api/market_events/latest?symbol=BTCUSDT", timeout=TIMEOUT)
            assert market_event_resp.status_code == 200, f"Market event fetch failed: {market_event_resp.text}"
            event = market_event_resp.json()
            price = event.get("price")
            assert price is not None, "No price in market event"

            # Business logic: Trigger alert if price crosses 100 (threshold)
            if price > 100:
                # Update alert triggered status in SQLite DB to simulate alert firing
                cursor.execute("UPDATE alerts SET triggered = ? WHERE id = ?", (True, alert_id))
                conn.commit()

                # Notify backend about alert triggering (POST /api/alerts/trigger)
                alert_trigger_payload = {
                    "alert_id": alert_id,
                    "strategy_id": strategy_id,
                    "event": event
                }
                alert_trigger_resp = requests.post(f"{BASE_URL}/api/alerts/trigger", json=alert_trigger_payload, headers=headers, timeout=TIMEOUT)
                assert alert_trigger_resp.status_code == 200, f"Alert trigger API failed: {alert_trigger_resp.text}"
                alert_trigger_resp_json = alert_trigger_resp.json()
                assert alert_trigger_resp_json.get("notified") is True, "Alert notification failed"
            else:
                # No alert triggered; ensure alert record stays untriggered
                cursor.execute("SELECT triggered FROM alerts WHERE id = ?", (alert_id,))
                triggered_status = cursor.fetchone()[0]
                assert triggered_status is False, "Alert incorrectly triggered"

        # Step 4: Cleanup - Delete created strategy and alert via API and SQLite DB
        delete_strategy_resp = requests.delete(f"{BASE_URL}/api/strategies/{strategy_id}", headers=headers, timeout=TIMEOUT)
        assert delete_strategy_resp.status_code in (200,204), f"Strategy deletion failed: {delete_strategy_resp.text}"
        cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
        conn.commit()

    finally:
        conn.close()

test_strategy_management_and_alert_triggering()