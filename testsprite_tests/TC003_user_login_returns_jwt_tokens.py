import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_user_login_returns_jwt_tokens():
    """
    Test user login flow:
    1. Register a new user
    2. Login with the registered credentials
    3. Verify that access_token and refresh_token are returned
    """
    # Step 1: Create a unique test user
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"logintest_{unique_id}@example.com"
    test_password = "StrongPass123!"

    register_payload = {
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password,
        "name": f"Login Test {unique_id}",
        "phone": "010-9876-5432",
    }

    register_url = f"{BASE_URL}/auth/register"
    try:
        reg_response = requests.post(
            register_url, json=register_payload, timeout=TIMEOUT
        )
        if reg_response.status_code != 200:
            raise AssertionError(f"Failed to register test user: {reg_response.text}")
    except requests.RequestException as e:
        raise AssertionError(f"Registration request failed: {e}")

    # Step 2: Login with the registered user
    login_url = f"{BASE_URL}/auth/login"
    headers = {"Content-Type": "application/json"}
    login_payload = {"email": test_email, "password": test_password}

    try:
        response = requests.post(
            login_url, json=login_payload, headers=headers, timeout=TIMEOUT
        )
        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Verify access_token
        assert "access_token" in data, "Response JSON missing 'access_token'"
        assert isinstance(data["access_token"], str) and data["access_token"], (
            "'access_token' must be a non-empty string"
        )

        # Verify refresh_token
        assert "refresh_token" in data, "Response JSON missing 'refresh_token'"
        assert isinstance(data["refresh_token"], str) and data["refresh_token"], (
            "'refresh_token' must be a non-empty string"
        )

        # Verify token_type
        assert data.get("token_type") == "bearer", "Token type should be 'bearer'"

        print("✅ User login successful with JWT tokens!")

    except requests.RequestException as e:
        raise AssertionError(f"Login request failed: {e}")


if __name__ == "__main__":
    test_user_login_returns_jwt_tokens()
    print("✅ TC003: User login test passed!")
