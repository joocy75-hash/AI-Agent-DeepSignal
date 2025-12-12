import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_refresh_access_token_with_valid_refresh_token():
    """
    Test refresh token flow:
    1. Register a new user
    2. Login to get access_token and refresh_token
    3. Use refresh_token to get a new access_token
    """
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"refreshtest_{unique_id}@example.com"
    test_password = "TestPass123!"

    # Step 1: Register a new user with correct schema
    register_url = f"{BASE_URL}/auth/register"
    register_payload = {
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password,
        "name": f"Refresh Test {unique_id}",
        "phone": "010-1111-2222",
    }

    try:
        register_response = requests.post(
            register_url, json=register_payload, timeout=TIMEOUT
        )
        assert register_response.status_code == 200, (
            f"User registration failed: {register_response.text}"
        )
    except requests.RequestException as e:
        raise AssertionError(f"Registration request failed: {e}")

    # Step 2: Login with the new user to get tokens
    login_url = f"{BASE_URL}/auth/login"
    login_payload = {
        "email": test_email,
        "password": test_password,
    }

    try:
        login_response = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"

        tokens = login_response.json()
        assert "refresh_token" in tokens, "Login response missing refresh_token"
        refresh_token = tokens["refresh_token"]

    except requests.RequestException as e:
        raise AssertionError(f"Login request failed: {e}")

    # Step 3: Use the refresh token to get a new access token
    # NOTE: The /auth/refresh endpoint expects refresh_token in request body, not header
    refresh_url = f"{BASE_URL}/auth/refresh"
    refresh_payload = {"refresh_token": refresh_token}

    try:
        refresh_response = requests.post(
            refresh_url, json=refresh_payload, timeout=TIMEOUT
        )
        assert refresh_response.status_code == 200, (
            f"Refresh token request failed: {refresh_response.text}"
        )

        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data, "Response missing new access_token"
        assert isinstance(refresh_data["access_token"], str), (
            "access_token should be a string"
        )
        assert len(refresh_data["access_token"]) > 0, "access_token should not be empty"

    except requests.RequestException as e:
        raise AssertionError(f"Refresh token request failed: {e}")


if __name__ == "__main__":
    test_refresh_access_token_with_valid_refresh_token()
    print("✅ TC004: Refresh token test passed!")
