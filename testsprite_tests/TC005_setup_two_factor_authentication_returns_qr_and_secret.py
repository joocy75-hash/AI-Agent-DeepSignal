import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_setup_2fa_returns_qr_and_secret():
    """
    Test 2FA setup flow:
    1. Register a new user
    2. Call /auth/2fa/setup endpoint with valid authentication
    3. Verify that secret, qr_code, and backup_codes are returned
    """
    # Step 1: Create a unique test user and get auth token
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"2fatest_{unique_id}@example.com"
    test_password = "StrongPass123!"

    register_payload = {
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password,
        "name": f"2FA Test {unique_id}",
        "phone": "010-2222-3333",
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

    # Step 2: Call 2FA setup endpoint
    # NOTE: Correct endpoint is /auth/2fa/setup (not /2fa/setup)
    setup_url = f"{BASE_URL}/auth/2fa/setup"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.post(setup_url, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Verify secret is returned
        assert "secret" in data, "Response should contain 'secret'"
        assert isinstance(data["secret"], str) and data["secret"], (
            "'secret' must be a non-empty string"
        )

        # Verify qr_code is returned (Base64 data URI)
        assert "qr_code" in data, "Response should contain 'qr_code'"
        assert isinstance(data["qr_code"], str), "'qr_code' must be a string"
        assert data["qr_code"].startswith("data:image/"), (
            "'qr_code' should be a data URI"
        )

        # Verify backup_codes are returned
        assert "backup_codes" in data, "Response should contain 'backup_codes'"
        assert isinstance(data["backup_codes"], list), "'backup_codes' must be a list"
        assert len(data["backup_codes"]) > 0, "'backup_codes' should not be empty"

    except requests.RequestException as e:
        raise AssertionError(f"2FA setup request failed: {e}")


if __name__ == "__main__":
    test_setup_2fa_returns_qr_and_secret()
    print("✅ TC005: 2FA setup test passed!")
