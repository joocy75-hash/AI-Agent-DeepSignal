import requests
import sqlite3
import threading
import time
from unittest import mock
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Helper functions to handle user creation and auth
def create_user_and_get_token(email, password):
    # Register user
    reg_resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
    )
    assert reg_resp.status_code == 201
    # Login user
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
    )
    assert login_resp.status_code == 200
    token = login_resp.json().get("access_token")
    assert token is not None
    return token

def get_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def test_user_settings_api_key_management_and_preferences():
    # Use unique user to avoid conflicts
    unique_id = uuid.uuid4().hex
    test_email = f"testuser_api_settings_{unique_id}@example.com"
    test_password = "StrongPassw0rd!"
    token = create_user_and_get_token(test_email, test_password)
    headers = get_headers(token)

    # Initial get user settings (should be defaults or empty)
    get_resp = requests.get(f"{BASE_URL}/api/account/settings", headers=headers, timeout=TIMEOUT)
    assert get_resp.status_code == 200
    settings_before = get_resp.json()
    assert isinstance(settings_before, dict)

    # Define new API keys and preferences to update
    new_settings_payload = {
        "api_keys": {
            "bitget_api_key": "mocked_bitget_api_key_123",
            "bitget_api_secret": "mocked_bitget_api_secret_abc",
            "bitget_passphrase": "mocked_passphrase_xyz"
        },
        "preferences": {
            "email_notifications": True,
            "dark_mode": True,
            "default_bot_type": "grid",
            "trade_execution_slippage": 0.05
        }
    }

    # Patch requests.post/send inside Bitget API calls to avoid real network calls
    # Here we mock requests.post globally in this test scope for demonstration
    with mock.patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json = lambda: {"mock": "response"}

        # Update user settings with new API keys and preferences
        put_resp = requests.put(f"{BASE_URL}/api/account/settings", headers=headers, json=new_settings_payload, timeout=TIMEOUT)
        assert put_resp.status_code == 200
        updated_settings = put_resp.json()
        assert updated_settings.get("api_keys") == new_settings_payload["api_keys"]
        assert updated_settings.get("preferences") == new_settings_payload["preferences"]

    # Retrieve again to ensure settings persist correctly
    get_after_resp = requests.get(f"{BASE_URL}/api/account/settings", headers=headers, timeout=TIMEOUT)
    assert get_after_resp.status_code == 200
    settings_after = get_after_resp.json()
    assert settings_after.get("api_keys") == new_settings_payload["api_keys"]
    assert settings_after.get("preferences") == new_settings_payload["preferences"]

    # Cleanup is not needed for user settings but if API keys are sensitive,
    # reset them by clearing settings back to empty or defaults (optional)
    reset_payload = {
        "api_keys": {},
        "preferences": {}
    }
    reset_resp = requests.put(f"{BASE_URL}/api/account/settings", headers=headers, json=reset_payload, timeout=TIMEOUT)
    assert reset_resp.status_code == 200

test_user_settings_api_key_management_and_preferences()
