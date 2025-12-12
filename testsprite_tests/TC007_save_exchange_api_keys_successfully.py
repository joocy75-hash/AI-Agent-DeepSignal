import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_save_exchange_api_keys():
    """
    Test saving exchange API keys:
    1. Register a new user
    2. Save API keys via /account/save_keys endpoint
    3. Verify the response indicates success

    Note: This test uses dummy API keys for testing purposes.
    In a real scenario, you would use actual exchange API keys.
    """
    # Step 1: Create a unique test user and get auth token
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"apikeys_{unique_id}@example.com"
    test_password = "StrongPass123!"

    register_payload = {
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password,
        "name": f"API Keys Test {unique_id}",
        "phone": "010-6666-7777",
    }

    register_url = f"{BASE_URL}/auth/register"
    try:
        reg_response = requests.post(
            register_url, json=register_payload, timeout=TIMEOUT
        )
        if reg_response.status_code != 200:
            raise AssertionError(f"Failed to register test user: {reg_response.text}")

        access_token = reg_response.json().get("access_token")
        if not access_token:
            raise AssertionError("No access_token in registration response")

    except requests.RequestException as e:
        raise AssertionError(f"Registration request failed: {e}")

    # Step 2: Save API keys
    # NOTE: Correct endpoint is /account/save_keys (not /account/keys)
    save_keys_url = f"{BASE_URL}/account/save_keys"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    # Use dummy API keys for testing (format validation will still apply)
    api_keys_payload = {
        "exchange": "bitget",
        "api_key": "test_api_key_12345678901234567890123456",
        "secret_key": "test_secret_key_1234567890123456789012345",
        "passphrase": "test_passphrase_123",
    }

    try:
        response = requests.post(
            save_keys_url, json=api_keys_payload, headers=headers, timeout=TIMEOUT
        )
        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Verify success response
        # API returns: {"message": "API 키가 저장되었습니다"}
        assert "message" in data or "success" in data, (
            "Response should indicate success"
        )

    except requests.RequestException as e:
        raise AssertionError(f"Save API keys request failed: {e}")


if __name__ == "__main__":
    test_save_exchange_api_keys()
    print("✅ TC007: Save exchange API keys test passed!")
