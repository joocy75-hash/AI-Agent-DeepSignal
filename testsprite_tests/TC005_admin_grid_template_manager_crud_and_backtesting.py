import requests
from unittest import mock

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

ADMIN_AUTH_TOKEN = "admin-test-jwt-token"  # Assume a valid admin JWT token for authentication in tests


def get_admin_headers():
    return {
        "Authorization": f"Bearer {ADMIN_AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# Mock for external Bitget REST API calls used internally by backtesting or bot creation logic
def mock_bitget_api(*args, **kwargs):
    # Simulate a successful API call returning dummy data
    class MockResponse:
        def json(self_inner):
            return {"result": "success"}

        @property
        def status_code(self_inner):
            return 200

        def raise_for_status(self_inner):
            pass

    return MockResponse()


@mock.patch("requests.get", side_effect=mock_bitget_api)
@mock.patch("requests.post", side_effect=mock_bitget_api)
@mock.patch("requests.put", side_effect=mock_bitget_api)
@mock.patch("requests.delete", side_effect=mock_bitget_api)
def test_admin_grid_template_manager_crud_and_backtesting(mock_delete, mock_put, mock_post, mock_get):
    # Use a try-finally block to ensure cleanup

    template_id = None
    try:
        # 1. Create a new grid bot template (Admin Create)
        create_payload = {
            "name": "Test Grid Template",
            "description": "Template for testing CRUD operations",
            "parameters": {
                "grid_levels": 5,
                "grid_spacing": 0.01,
                "grid_interval": 60,
                "bot_type": "grid",
                "initial_investment": 1000
            },
            "is_active": True
        }
        create_resp = requests.post(
            f"{BASE_URL}/admin/grid-templates",
            headers=get_admin_headers(),
            json=create_payload,
            timeout=TIMEOUT,
        )
        assert create_resp.status_code == 201 or create_resp.status_code == 200
        created_data = create_resp.json()
        assert "id" in created_data
        template_id = created_data["id"]
        assert created_data["name"] == create_payload["name"]
        assert created_data["parameters"]["grid_levels"] == 5
        assert created_data["parameters"].get("grid_interval") == 60

        # 2. Update the grid bot template (Admin Update)
        update_payload = {
            "name": "Test Grid Template Updated",
            "description": "Updated description for CRUD test",
            "parameters": {
                "grid_levels": 10,
                "grid_spacing": 0.005,
                "grid_interval": 30,
                "bot_type": "grid",
                "initial_investment": 2000
            },
            "is_active": False
        }
        update_resp = requests.put(
            f"{BASE_URL}/admin/grid-templates/{template_id}",
            headers=get_admin_headers(),
            json=update_payload,
            timeout=TIMEOUT,
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()
        assert updated_data["name"] == update_payload["name"]
        assert updated_data["parameters"]["grid_levels"] == 10
        assert updated_data["parameters"].get("grid_interval") == 30
        assert updated_data["is_active"] is False

        # 3. Run backtest on the updated template (Admin Backtesting)
        backtest_payload = {
            "template_id": template_id,
            "historical_data_start": "2024-01-01T00:00:00Z",
            "historical_data_end": "2024-02-01T00:00:00Z",
            "initial_balance": 10000
        }
        backtest_resp = requests.post(
            f"{BASE_URL}/admin/grid-templates/{template_id}/backtest",
            headers=get_admin_headers(),
            json=backtest_payload,
            timeout=TIMEOUT,
        )
        assert backtest_resp.status_code == 200
        backtest_result = backtest_resp.json()
        # Validate backtest response structure and data presence
        assert "performance_metrics" in backtest_result
        assert backtest_result["performance_metrics"].get("total_return") is not None
        assert backtest_result["performance_metrics"].get("max_drawdown") is not None
        assert "trades" in backtest_result
        assert isinstance(backtest_result["trades"], list)

        # 4. Validate the template appears with updated data on get (Admin Read)
        get_resp = requests.get(
            f"{BASE_URL}/admin/grid-templates/{template_id}",
            headers=get_admin_headers(),
            timeout=TIMEOUT,
        )
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["name"] == update_payload["name"]
        assert get_data["parameters"]["grid_spacing"] == 0.005
        assert get_data["parameters"].get("grid_interval") == 30
        assert get_data["is_active"] is False

    finally:
        # 5. Delete the grid bot template (Admin Delete)
        if template_id:
            del_resp = requests.delete(
                f"{BASE_URL}/admin/grid-templates/{template_id}",
                headers=get_admin_headers(),
                timeout=TIMEOUT,
            )
            assert del_resp.status_code == 204 or del_resp.status_code == 200
            # Confirm deletion by attempting to get the template
            get_after_del_resp = requests.get(
                f"{BASE_URL}/admin/grid-templates/{template_id}",
                headers=get_admin_headers(),
                timeout=TIMEOUT,
            )
            assert get_after_del_resp.status_code == 404


test_admin_grid_template_manager_crud_and_backtesting()
