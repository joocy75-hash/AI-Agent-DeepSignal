import requests
import time
import jwt

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_user_authentication_oauth_jwt_handling():
    session = requests.Session()

    # 1. Test email/password login (Register and login)
    user_email = "testuser@example.com"
    user_password = "TestPass123!"

    # Cleanup function to delete user if created during test
    user_id = None
    tokens = {}

    try:
        # Register user
        register_payload = {
            "email": user_email,
            "password": user_password
        }
        r = session.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=TIMEOUT)
        # Accept 201 Created or 400 if already registered (but assume test DB)
        assert r.status_code in (201, 400)
        if r.status_code == 201:
            user_id = r.json().get("id")
        elif r.status_code == 400:
            # Try to login anyway if exists
            pass
        else:
            assert False, "Unexpected register response"

        # Login user with email/password
        login_payload = {
            "email": user_email,
            "password": user_password
        }
        r = session.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=TIMEOUT)
        assert r.status_code == 200, f"Login failed with status {r.status_code}"
        login_data = r.json()
        assert "access_token" in login_data and "refresh_token" in login_data
        tokens['jwt_access_token'] = login_data["access_token"]
        tokens['jwt_refresh_token'] = login_data["refresh_token"]

        # Validate JWT token (decode without verification to inspect claims)
        try:
            decoded_token = jwt.decode(tokens['jwt_access_token'], options={"verify_signature": False})
            assert "sub" in decoded_token
            assert decoded_token.get("exp") > time.time()
        except Exception as ex:
            assert False, f"JWT token decoding failed: {ex}"

        # 2. Test OAuth login via Google
        # Mock the OAuth token verification response by sending a fake token to the backend.
        # Assume endpoint: POST /auth/oauth/google with payload { "token": "mock_google_token" }
        google_oauth_payload = {"token": "mock_google_token"}
        r = session.post(f"{BASE_URL}/auth/oauth/google", json=google_oauth_payload, timeout=TIMEOUT)
        assert r.status_code == 200, f"Google OAuth login failed with status {r.status_code}"
        google_oauth_data = r.json()
        assert "access_token" in google_oauth_data and "refresh_token" in google_oauth_data

        # 3. Test OAuth login via Kakao
        kakao_oauth_payload = {"token": "mock_kakao_token"}
        r = session.post(f"{BASE_URL}/auth/oauth/kakao", json=kakao_oauth_payload, timeout=TIMEOUT)
        assert r.status_code == 200, f"Kakao OAuth login failed with status {r.status_code}"
        kakao_oauth_data = r.json()
        assert "access_token" in kakao_oauth_data and "refresh_token" in kakao_oauth_data

        # 4. Validate JWT token expiration and refresh flow
        # Assume refresh token endpoint: POST /auth/refresh with payload { "refresh_token": <token> }

        # Use the refresh token from email login
        refresh_payload = {"refresh_token": tokens['jwt_refresh_token']}
        r = session.post(f"{BASE_URL}/auth/refresh", json=refresh_payload, timeout=TIMEOUT)
        assert r.status_code == 200, f"Refresh token failed with status {r.status_code}"
        refresh_data = r.json()
        assert "access_token" in refresh_data

        new_access_token = refresh_data["access_token"]
        decoded_new_token = jwt.decode(new_access_token, options={"verify_signature": False})
        assert decoded_new_token.get("exp") > time.time()

        # 5. Validate access token usage on a protected endpoint
        # Assume GET /dashboard requires Bearer token auth
        headers = {"Authorization": f"Bearer {new_access_token}"}
        r = session.get(f"{BASE_URL}/dashboard", headers=headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"Access with JWT token failed, status {r.status_code}"

        # 6. Test expired token behavior (simulate by using an expired token)
        # Fake expired token by setting exp in past and encoding
        expired_token = jwt.encode({"sub": "user", "exp": int(time.time()) - 10}, "secret", algorithm="HS256")

        headers_expired = {"Authorization": f"Bearer {expired_token}"}
        r = session.get(f"{BASE_URL}/dashboard", headers=headers_expired, timeout=TIMEOUT)
        # Should be unauthorized or forbidden
        assert r.status_code in (401, 403), f"Expected 401/403 for expired token, got {r.status_code}"

    finally:
        # Cleanup: delete user created (if applicable)
        if user_id:
            try:
                # Need admin or token to delete user, assume admin token or user token can delete own account
                admin_token = None

                # Try to login admin or reuse user token for deletion
                admin_login_payload = {"email": "admin@example.com", "password": "AdminPass123!"}
                admin_login_resp = session.post(f"{BASE_URL}/auth/login", json=admin_login_payload, timeout=TIMEOUT)
                if admin_login_resp.status_code == 200:
                    admin_token = admin_login_resp.json().get("access_token")
                else:
                    admin_token = tokens.get('jwt_access_token')

                if admin_token:
                    del_headers = {"Authorization": f"Bearer {admin_token}"}
                    del_resp = session.delete(f"{BASE_URL}/users/{user_id}", headers=del_headers, timeout=TIMEOUT)
                    # If deletion not allowed, ignore error
                    if del_resp.status_code not in (200, 204, 404):
                        pass
            except Exception:
                pass


test_user_authentication_oauth_jwt_handling()