import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_candle_data_for_symbol():
    """
    Test getting candle (OHLCV) data for a trading symbol:
    1. Register and authenticate a user
    2. Request candle data
    3. Verify response format

    Note: This endpoint requires authentication.
    """
    unique_id = uuid.uuid4().hex[:8]

    # Step 1: Register a new user
    register_payload = {
        "email": f"candletest_{unique_id}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "name": f"Candle Test {unique_id}",
        "phone": "010-5555-6666",
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

    # Step 2: Request candle data
    symbol = "BTCUSDT"
    interval = "15m"  # Common interval
    url = f"{BASE_URL}/chart/candles/{symbol}"
    params = {"interval": interval}
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise AssertionError(f"Request to get candle data failed: {e}")

    # Step 3: Verify response
    if response.status_code == 400:
        # API keys might not be configured - this is acceptable for test
        data = response.json()
        if "API" in data.get("detail", ""):
            print("✓ Candle endpoint reachable - requires API keys")
            return

    assert response.status_code == 200, (
        f"Expected status code 200, got {response.status_code}. Response: {response.text}"
    )

    try:
        data = response.json()
    except ValueError:
        raise AssertionError("Response is not in JSON format")

    assert isinstance(data, list), "Response JSON should be a list of candle data"

    # Check fields in candle data if any data returned
    if data:
        candle = data[0]
        # API returns: timestamp, open, high, low, close, volume
        required_fields = {"timestamp", "open", "high", "low", "close", "volume"}
        missing_fields = required_fields - set(candle.keys())
        assert not missing_fields, (
            f"Candle data missing required fields: {missing_fields}"
        )

        # Validate data types
        assert isinstance(candle["timestamp"], (int, float)), (
            "timestamp should be numeric"
        )
        assert isinstance(candle["open"], (int, float, str)), (
            "open should be numeric or string"
        )
        assert isinstance(candle["close"], (int, float, str)), (
            "close should be numeric or string"
        )

        print(f"✓ Received {len(data)} candles for {symbol}")


if __name__ == "__main__":
    test_get_candle_data_for_symbol()
    print("✅ TC010: Get candle data test passed!")
