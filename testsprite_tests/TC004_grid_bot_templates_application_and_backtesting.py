import requests
from unittest import mock
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Mock responses for external Bitget REST API calls used internally in bot creation and position closing logic
# Assume the backend calls Bitget API endpoints like /api/bitget/positions/close and /api/bitget/orders/create etc.
# We'll patch requests.post or requests.get used by backend during test via side_effect mocks.

def test_grid_bot_templates_application_and_backtesting():
    """
    Validate applying AI-recommended grid bot templates and running backtests with accurate results.
    Mock Bitget external API calls to avoid real network calls.
    Use SQLite DB (assumed by backend).
    Focus on position closing logic and bot creation flow.
    """
    # Authentication: assuming test user credentials and token generation endpoint
    # First, login or register user to get JWT token for authorization
    # For this test, we'll create a test user and get token or use a stub token if applicable.
    # Here we simulate login and obtaining a token.
    auth_url = f"{BASE_URL}/api/auth/login"
    login_payload = {"email": "testuser@example.com", "password": "TestPassword123!"}
    
    with requests.Session() as session:
        login_resp = session.post(auth_url, json=login_payload, timeout=TIMEOUT)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        login_data = login_resp.json()
        token = login_data.get("access_token")
        assert token, "No access token returned on login"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Step 1: Get list of AI-recommended grid bot templates
        templates_url = f"{BASE_URL}/api/grid-templates/recommended"
        templates_resp = session.get(templates_url, headers=headers, timeout=TIMEOUT)
        assert templates_resp.status_code == 200, f"Failed to get recommended templates: {templates_resp.text}"
        templates = templates_resp.json()
        assert isinstance(templates, list) and len(templates) > 0, "No recommended grid bot templates found"
        
        # Pick a template to apply
        template_to_apply = templates[0]
        template_id = template_to_apply.get("id")
        assert template_id, "Selected template missing id"

        # Mock external Bitget API calls
        # Assuming backend calls 'requests.post' to Bitget API endpoints on bot creation & position closing
        # We'll patch 'requests.post' to simulate Bitget API responses for these calls
        
        def mock_bitget_post(url, *args, **kwargs):
            # Simulate Bitget API endpoints responses
            if url.startswith("https://api.bitget.com/api/spot/v1/positions/close"):
                # Simulate successful position close response
                return mock.Mock(status_code=200, json=lambda: {"success": True, "message": "Position closed"})
            if url.startswith("https://api.bitget.com/api/spot/v1/orders"):
                # Simulate order creation success
                return mock.Mock(status_code=200, json=lambda: {"success": True, "order_id": "123456"})
            # Default mock successful response for other Bitget API POST calls
            return mock.Mock(status_code=200, json=lambda: {"success": True})

        with mock.patch("requests.post", side_effect=mock_bitget_post):

            # Step 2: Apply selected template to create a grid bot
            apply_url = f"{BASE_URL}/api/bots/grid"
            apply_payload = {
                "template_id": template_id,
                "bot_name": "Test Grid Bot Application",
                "initial_balance": 1000,
                "parameters": template_to_apply.get("parameters", {}),
            }
            create_resp = session.post(apply_url, headers=headers, json=apply_payload, timeout=TIMEOUT)
            assert create_resp.status_code == 201, f"Failed to create grid bot: {create_resp.text}"
            bot_data = create_resp.json()
            bot_id = bot_data.get("id")
            assert bot_id, "Created grid bot missing id"

            try:
                # Step 3: Run backtest on the applied template/bot with historical data parameters
                backtest_url = f"{BASE_URL}/api/grid-templates/{template_id}/backtest"
                backtest_params = {
                    "start_date": "2023-01-01",
                    "end_date": "2023-06-01",
                    "initial_balance": 1000,
                    "parameters": template_to_apply.get("parameters", {}),
                }
                backtest_resp = session.post(backtest_url, headers=headers, json=backtest_params, timeout=TIMEOUT)
                assert backtest_resp.status_code == 200, f"Backtest failed: {backtest_resp.text}"
                backtest_result = backtest_resp.json()

                # Validate backtest result contains accurate performance results and relevant metrics
                for key in ["total_return", "max_drawdown", "sharpe_ratio", "trades"]:
                    assert key in backtest_result, f"Backtest result missing key: {key}"

                # Validate trades parameter handling - each trade should have required fields
                trades = backtest_result.get("trades", [])
                assert isinstance(trades, list), "Backtest trades should be a list"
                if trades:
                    trade = trades[0]
                    for field in ["entry_price", "exit_price", "profit_loss", "quantity"]:
                        assert field in trade, f"Trade missing field: {field}"

                # Step 4: Test position closing logic via API call on the created bot (mocked Bitget closes position)
                close_position_url = f"{BASE_URL}/api/bots/{bot_id}/positions/close"
                close_resp = session.post(close_position_url, headers=headers, timeout=TIMEOUT)
                assert close_resp.status_code == 200, f"Position close failed: {close_resp.text}"
                close_data = close_resp.json()
                assert close_data.get("success") is True, "Position closing was not successful"

            finally:
                # Cleanup: delete created bot after test to keep DB clean
                delete_url = f"{BASE_URL}/api/bots/{bot_id}"
                del_resp = session.delete(delete_url, headers=headers, timeout=TIMEOUT)
                assert del_resp.status_code == 204, f"Failed to delete grid bot: {del_resp.text}"


test_grid_bot_templates_application_and_backtesting()