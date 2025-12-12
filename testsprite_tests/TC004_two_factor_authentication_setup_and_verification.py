import requests
import uuid
import pyotp

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_two_factor_authentication_setup_and_verification():
    """
    Test 2FA setup and verification flow:
    1. Register a new user (with correct schema)
    2. Setup 2FA to get QR code and secret
    3. Generate a valid TOTP code using the secret
    4. Verify the code to enable 2FA
    """
    # Create a unique test user with correct schema
    unique_id = uuid.uuid4().hex[:8]
    email = f"2fatest_{unique_id}@example.com"
    password = "TestPassword123!"  # Must include special character

    try:
        # Register user with correct schema
        register_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": email,
                "password": password,
                "password_confirm": password,
                "name": f"2FA Test User {unique_id}",
                "phone": "010-1234-5678",
            },
            timeout=TIMEOUT,
        )
        assert register_resp.status_code == 200, (
            f"User registration failed: {register_resp.status_code} {register_resp.text}"
        )

        # Get access token from registration response
        reg_data = register_resp.json()
        access_token = reg_data.get("access_token")
        assert access_token, "No access_token in registration response"

        headers = {"Authorization": f"Bearer {access_token}"}

        # Setup 2FA - correct endpoint is /auth/2fa/setup
        setup_resp = requests.post(
            f"{BASE_URL}/auth/2fa/setup",
            headers=headers,
            timeout=TIMEOUT,
        )
        assert setup_resp.status_code == 200, f"2FA setup failed: {setup_resp.text}"
        setup_data = setup_resp.json()
        assert "qr_code" in setup_data and "secret" in setup_data, (
            "QR code or secret missing in 2FA setup response"
        )

        secret = setup_data["secret"]

        # Generate a valid TOTP code using the returned secret
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Verify 2FA code - correct endpoint is /auth/2fa/verify
        verify_resp = requests.post(
            f"{BASE_URL}/auth/2fa/verify",
            headers=headers,
            json={"code": code},
            timeout=TIMEOUT,
        )
        assert verify_resp.status_code == 200, (
            f"2FA verification failed: {verify_resp.text}"
        )

        print("✅ 2FA setup and verification successful!")

    except Exception as e:
        raise AssertionError(f"Test failed: {e}")


if __name__ == "__main__":
    test_two_factor_authentication_setup_and_verification()
    print("✅ TC004: 2FA setup and verification test passed!")
