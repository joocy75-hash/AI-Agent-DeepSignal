import requests
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Mocked responses for Bitget REST API calls
def mock_bitget_api(*args, **kwargs):
    class MockResponse:
        def json(self):
            return {"result": "success"}
        @property
        def status_code(self):
            return 200
        @property
        def text(self):
            return str(self.json())
    return MockResponse()

def test_bot_management_create_start_stop_monitor():
    # Mock Bitget external API calls inside bot operations
    with mock.patch("requests.post", side_effect=mock_bitget_api), mock.patch("requests.get", side_effect=mock_bitget_api):
        # Step 1: Create a Grid Bot
        create_payload = {
            "bot_type": "grid",
            "name": "Test Grid Bot",
            "config": {
                "grid_size": 10,
                "start_price": 100,
                "end_price": 150,
                "base_currency": "USDT",
                "quote_currency": "BTC"
            }
        }
        create_response = requests.post(f"{BASE_URL}/api/bots", json=create_payload, timeout=TIMEOUT)
        assert create_response.status_code == 201, f"Bot creation failed: {create_response.text}"
        bot = create_response.json()
        bot_id = bot.get("id")
        assert bot_id is not None, "Bot ID not returned in creation response"

        try:
            # Step 2: Start the Bot
            start_response = requests.post(f"{BASE_URL}/api/bots/{bot_id}/start", timeout=TIMEOUT)
            assert start_response.status_code == 200, f"Bot start failed: {start_response.text}"
            start_data = start_response.json()
            assert start_data.get("status") == "running", "Bot status is not running after start"

            # Step 3: Monitor Bot Status - Should be 'running'
            status_response = requests.get(f"{BASE_URL}/api/bots/{bot_id}/status", timeout=TIMEOUT)
            assert status_response.status_code == 200, f"Failed to get bot status: {status_response.text}"
            status_data = status_response.json()
            assert status_data.get("status") == "running", "Bot status not running while started"

            # Step 4: Stop the Bot
            stop_response = requests.post(f"{BASE_URL}/api/bots/{bot_id}/stop", timeout=TIMEOUT)
            assert stop_response.status_code == 200, f"Bot stop failed: {stop_response.text}"
            stop_data = stop_response.json()
            assert stop_data.get("status") == "stopped", "Bot status is not stopped after stop"

            # Step 5: Check Bot Status - Should be 'stopped'
            status_response_2 = requests.get(f"{BASE_URL}/api/bots/{bot_id}/status", timeout=TIMEOUT)
            assert status_response_2.status_code == 200, f"Failed to get bot status after stop: {status_response_2.text}"
            status_data_2 = status_response_2.json()
            assert status_data_2.get("status") == "stopped", "Bot status not stopped after stop"

            # Step 6: Test Position Closing Logic - simulate closing positions if applicable
            # For this test, assume endpoint to close positions: POST /api/bots/{bot_id}/positions/close
            close_response = requests.post(f"{BASE_URL}/api/bots/{bot_id}/positions/close", timeout=TIMEOUT)
            assert close_response.status_code == 200, f"Closing positions failed: {close_response.text}"
            close_data = close_response.json()
            assert close_data.get("result") == "positions_closed", "Positions were not closed correctly"

            # Step 7: Validate Data Persistence by fetching the bot info again
            get_bot_response = requests.get(f"{BASE_URL}/api/bots/{bot_id}", timeout=TIMEOUT)
            assert get_bot_response.status_code == 200, f"Fetching bot info failed: {get_bot_response.text}"
            get_bot_data = get_bot_response.json()
            assert get_bot_data.get("id") == bot_id, "Fetched bot ID does not match"
            assert get_bot_data.get("name") == "Test Grid Bot", "Bot name mismatch after operations"
            assert get_bot_data.get("status") == "stopped", "Bot status mismatch after stop"

        finally:
            # Cleanup: Delete the created bot to maintain test isolation
            delete_response = requests.delete(f"{BASE_URL}/api/bots/{bot_id}", timeout=TIMEOUT)
            assert delete_response.status_code in (200, 204), f"Failed to delete bot: {delete_response.text}"


test_bot_management_create_start_stop_monitor()
