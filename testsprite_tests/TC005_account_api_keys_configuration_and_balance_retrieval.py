import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_account_api_keys_configuration_and_balance_retrieval():
    """
    Test account API keys configuration and balance retrieval:
    1. Register a new test user (with correct schema)
    2. Attempt to get balance before API keys configured (should fail)
    3. Save API keys via /account/save_keys
    4. Verify API keys were saved (balance still may fail with dummy keys)
    """
    # Step 1: Register a new test user with correct schema
    unique_id = uuid.uuid4().hex[:8]
    register_url = f"{BASE_URL}/auth/register"
    unique_email = f"apikeys_{unique_id}@example.com"
    password = "TestPass123!"

    register_data = {
        "email": unique_email,
        "password": password,
        "password_confirm": password,
        "name": f"API Keys Test {unique_id}",
        "phone": "010-2222-3333",
    }
    register_resp = requests.post(register_url, json=register_data, timeout=TIMEOUT)
    assert register_resp.status_code == 200, (
        f"User registration failed: {register_resp.status_code} {register_resp.text}"
    )

    # Get access token from registration response
    reg_json = register_resp.json()
    access_token = reg_json.get("access_token")
    assert access_token, "No access_token returned from registration"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Step 2: Attempt to get balance before API keys configured - should return 400 error
    balance_url = f"{BASE_URL}/account/balance"
    balance_resp = requests.get(balance_url, headers=headers, timeout=TIMEOUT)
    assert balance_resp.status_code == 400, (
        f"Expected 400 status for balance when API keys not configured, got {balance_resp.status_code}. "
        f"Response: {balance_resp.text}"
    )

    # Step 3: Configure API keys via /account/save_keys (correct endpoint)
    keys_url = f"{BASE_URL}/account/save_keys"
    # Use dummy API keys for testing (format requirements apply)
    keys_data = {
        "exchange": "bitget",
        "api_key": "test_api_key_12345678901234567890123456",
        "secret_key": "test_secret_key_1234567890123456789012345",
        "passphrase": "test_passphrase_123",
    }
    keys_resp = requests.post(
        keys_url, headers=headers, json=keys_data, timeout=TIMEOUT
    )
    assert keys_resp.status_code == 200, (
        f"Failed to save API keys: {keys_resp.status_code} {keys_resp.text}"
    )

    # Step 4: Verify balance endpoint behavior after keys are saved
    # Note: With dummy keys, actual balance retrieval may still fail,
    # but the endpoint should now attempt to connect to exchange
    balance_resp_after = requests.get(balance_url, headers=headers, timeout=TIMEOUT)

    # Accept 200 (success) or 500 (exchange connection error with dummy keys)
    # The important thing is that it's no longer 400 (keys not configured)
    if balance_resp_after.status_code == 200:
        balance_json = balance_resp_after.json()
        assert isinstance(balance_json, dict), "Balance response is not a JSON object"
        print("✅ Balance retrieved successfully!")
    elif balance_resp_after.status_code == 500:
        # Expected with dummy keys - exchange connection failed
        print(
            "✅ API keys saved, balance fetch failed due to invalid keys (expected with dummy keys)"
        )
    else:
        raise AssertionError(
            f"Unexpected status after saving keys: {balance_resp_after.status_code}"
        )


if __name__ == "__main__":
    test_account_api_keys_configuration_and_balance_retrieval()
    print("✅ TC005: Account API keys configuration test passed!")
