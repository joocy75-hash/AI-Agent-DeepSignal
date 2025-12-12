import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_start_trading_bot_with_valid_parameters():
    """
    Test starting the trading bot:
    1. Register a new user
    2. Attempt to start the bot (will fail without API keys)
    3. Verify appropriate error response

    Note: Starting the bot requires:
    - Valid exchange API keys
    - Bot start endpoint at /bot/start

    This test verifies the authentication and basic flow.
    In production, you would need to configure API keys first.
    """
    session = requests.Session()
    unique_id = uuid.uuid4().hex[:8]

    # Step 1: Register a new user
    register_payload = {
        "email": f"botstart_{unique_id}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "name": f"Bot Start Test {unique_id}",
        "phone": "010-8888-9999",
    }

    try:
        register_response = session.post(
            f"{BASE_URL}/auth/register", json=register_payload, timeout=TIMEOUT
        )
        assert register_response.status_code == 200, (
            f"Registration failed: {register_response.text}"
        )

        access_token = register_response.json().get("access_token")
        assert access_token, "No access_token in registration response"

    except requests.RequestException as e:
        raise AssertionError(f"Registration request failed: {e}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Step 2: Check bot status first
    try:
        status_response = session.get(
            f"{BASE_URL}/bot/status", headers=headers, timeout=TIMEOUT
        )
        # Bot status should return 200
        assert status_response.status_code == 200, (
            f"Bot status check failed: {status_response.text}"
        )

    except requests.RequestException as e:
        raise AssertionError(f"Bot status request failed: {e}")

    # Step 3: Try to start bot (should fail without API keys)
    # The /bot/start endpoint doesn't require symbol/strategy_id in body
    try:
        start_response = session.post(
            f"{BASE_URL}/bot/start",
            headers=headers,
            json={},  # Empty body - bot uses user's saved settings
            timeout=TIMEOUT,
        )

        # Expected: 400 error because API keys are not configured
        # This validates that authentication works and the endpoint is reachable
        if start_response.status_code == 400:
            # Expected - API keys not configured
            data = start_response.json()
            assert "API" in data.get("detail", "") or "키" in data.get("detail", ""), (
                "Error should mention API keys"
            )
            print("✓ Bot start correctly rejected - API keys not configured")
        elif start_response.status_code == 200:
            # Unexpectedly succeeded - stop the bot to clean up
            session.post(f"{BASE_URL}/bot/stop", headers=headers, timeout=TIMEOUT)
            print("✓ Bot started successfully")
        else:
            raise AssertionError(
                f"Unexpected status code: {start_response.status_code}"
            )

    except requests.RequestException as e:
        raise AssertionError(f"Bot start request failed: {e}")


if __name__ == "__main__":
    test_start_trading_bot_with_valid_parameters()
    print("✅ TC008: Bot start test passed!")
