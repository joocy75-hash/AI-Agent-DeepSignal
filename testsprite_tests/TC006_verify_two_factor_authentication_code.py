import requests
import uuid
import pyotp

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_verify_2fa_code():
    """
    Test 2FA verification flow:
    1. Register a new user
    2. Setup 2FA to get the secret
    3. Generate a valid TOTP code using the secret
    4. Verify the code via /auth/2fa/verify endpoint

    Note: This test requires the 'pyotp' library.
    Install with: pip install pyotp
    """
    # Step 1: Create a unique test user and get auth token
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"2faverify_{unique_id}@example.com"
    test_password = "StrongPass123!"

    register_payload = {
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password,
        "name": f"2FA Verify {unique_id}",
        "phone": "010-4444-5555",
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    # Step 2: Setup 2FA to get the secret
    setup_url = f"{BASE_URL}/auth/2fa/setup"
    try:
        setup_response = requests.post(setup_url, headers=headers, timeout=TIMEOUT)
        if setup_response.status_code != 200:
            raise AssertionError(f"Failed to setup 2FA: {setup_response.text}")

        setup_data = setup_response.json()
        secret = setup_data.get("secret")
        if not secret:
            raise AssertionError("No secret in 2FA setup response")

    except requests.RequestException as e:
        raise AssertionError(f"2FA setup request failed: {e}")

    # Step 3: Generate a valid TOTP code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    # Step 4: Verify the code
    # NOTE: Correct endpoint is /auth/2fa/verify (not /2fa/verify)
    verify_url = f"{BASE_URL}/auth/2fa/verify"
    verify_payload = {"code": valid_code}

    try:
        response = requests.post(
            verify_url, json=verify_payload, headers=headers, timeout=TIMEOUT
        )
        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Verify success message
        assert "message" in data, "Response should contain 'message'"
        assert "성공" in data["message"] or "success" in data["message"].lower(), (
            f"Expected success message, got: {data['message']}"
        )

    except requests.RequestException as e:
        raise AssertionError(f"2FA verify request failed: {e}")


if __name__ == "__main__":
    test_verify_2fa_code()
    print("✅ TC006: 2FA verification test passed!")
