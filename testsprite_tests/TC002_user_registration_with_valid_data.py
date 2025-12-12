import requests
import uuid

BASE_URL = "http://localhost:8000"
REGISTER_ENDPOINT = "/auth/register"
TIMEOUT = 30


def test_user_registration_with_valid_data():
    """
    Test user registration with valid data.

    Required fields:
    - email: Valid email address
    - password: Strong password (min 8 chars, upper/lower case, number, special char)
    - password_confirm: Must match password
    - name: User name (2-50 chars)
    - phone: Phone number (10-13 digits)
    """
    url = f"{BASE_URL}{REGISTER_ENDPOINT}"
    # Generate unique email to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    payload = {
        "email": f"testuser_{unique_id}@example.com",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "name": f"Test User {unique_id}",
        "phone": "010-1234-5678",
    }
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        # API returns 200 with access_token on successful registration
        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        )

        # Verify response contains access_token
        data = response.json()
        assert "access_token" in data, "Response should contain 'access_token'"
        assert data["token_type"] == "bearer", "Token type should be 'bearer'"

        print("✅ User registration successful!")

    except requests.RequestException as e:
        raise AssertionError(f"Request to {url} failed: {e}")


if __name__ == "__main__":
    test_user_registration_with_valid_data()
    print("✅ TC002: User registration test passed!")
