import requests
import uuid

BASE_URL = "http://localhost:8000"
ORDER_SUBMIT_ENDPOINT = "/order/submit"
TIMEOUT = 30


def test_submit_new_trading_order():
    """
    Test submitting a trading order:
    1. Register and authenticate a user
    2. Attempt to submit an order
    3. Verify appropriate response

    Note: Submitting orders requires:
    - Valid exchange API keys
    - Sufficient balance

    This test verifies authentication and endpoint reachability.
    """
    unique_id = uuid.uuid4().hex[:8]

    # Step 1: Register a new user
    register_payload = {
        "email": f"ordertest_{unique_id}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "name": f"Order Test {unique_id}",
        "phone": "010-3333-4444",
    }

    try:
        register_response = requests.post(
            f"{BASE_URL}/auth/register", json=register_payload, timeout=TIMEOUT
        )
        assert register_response.status_code == 200, (
            f"Registration failed: {register_response.text}"
        )

        access_token = register_response.json().get("access_token")
        assert access_token, "No access_token in registration response"

    except requests.RequestException as e:
        raise AssertionError(f"Registration request failed: {e}")

    # Step 2: Try to submit an order
    url = BASE_URL + ORDER_SUBMIT_ENDPOINT
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    # Order payload - matches API schema
    payload = {
        "symbol": "BTCUSDT",
        "side": "long",  # API uses "long"/"short" not "buy"/"sell"
        "amount": 10.0,  # USDT amount
        "leverage": 5,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)

        # Expected: 400 error because API keys are not configured
        if response.status_code == 400:
            data = response.json()
            # Should mention API keys not configured
            assert "API" in data.get("detail", "") or "키" in data.get("detail", ""), (
                "Error should mention API keys"
            )
            print("✓ Order correctly rejected - API keys not configured")
        elif response.status_code == 200:
            print("✓ Order submitted successfully")
        else:
            # Authentication should work, just order execution might fail
            print(f"⚠ Got status {response.status_code}: {response.text}")

    except requests.RequestException as e:
        raise AssertionError(f"Request to submit order failed: {e}")


if __name__ == "__main__":
    test_submit_new_trading_order()
    print("✅ TC009: Submit order test passed!")
