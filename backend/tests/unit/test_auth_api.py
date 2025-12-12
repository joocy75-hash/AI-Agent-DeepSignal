"""
Unit tests for authentication API endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.unit
@pytest.mark.api
class TestAuthRegister:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        payload = {
            "email": "test@example.com",
            "password": "Test1234!@#",
            "password_confirm": "Test1234!@#",
            "name": "Test User",
            "phone": "01012345678",
        }

        response = await async_client.post("/auth/register", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client: AsyncClient):
        """Test registration with duplicate email fails."""
        payload = {
            "email": "duplicate@example.com",
            "password": "Test1234!@#",
            "password_confirm": "Test1234!@#",
            "name": "First User",
            "phone": "01012345678",
        }

        # First registration
        response1 = await async_client.post("/auth/register", json=payload)
        assert response1.status_code == 200

        # Second registration with same email
        payload["name"] = "Second User"
        response2 = await async_client.post("/auth/register", json=payload)
        assert response2.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_register_password_mismatch(self, async_client: AsyncClient):
        """Test registration with password mismatch fails."""
        payload = {
            "email": "mismatch@example.com",
            "password": "Test1234!@#",
            "password_confirm": "DifferentPassword!@#",
            "name": "Test User",
            "phone": "01012345678",
        }

        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password fails."""
        payload = {
            "email": "weak@example.com",
            "password": "123456",  # Too weak
            "password_confirm": "123456",
            "name": "Test User",
            "phone": "01012345678",
        }

        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email fails."""
        payload = {
            "email": "not-an-email",
            "password": "Test1234!@#",
            "password_confirm": "Test1234!@#",
            "name": "Test User",
            "phone": "01012345678",
        }

        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 422  # Validation error


@pytest.mark.unit
@pytest.mark.api
class TestAuthLogin:
    """Tests for user login endpoint."""

    @pytest.fixture
    async def registered_user(self, async_client: AsyncClient):
        """Create a registered user for login tests."""
        payload = {
            "email": "login_test@example.com",
            "password": "Test1234!@#",
            "password_confirm": "Test1234!@#",
            "name": "Login Test User",
            "phone": "01012345678",
        }
        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 200
        return payload

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, registered_user):
        """Test successful user login."""
        payload = {
            "email": registered_user["email"],
            "password": registered_user["password"],
        }

        response = await async_client.post("/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client: AsyncClient, registered_user):
        """Test login with wrong password fails."""
        payload = {
            "email": registered_user["email"],
            "password": "WrongPassword!@#",
        }

        response = await async_client.post("/auth/login", json=payload)
        assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user fails."""
        payload = {
            "email": "nonexistent@example.com",
            "password": "SomePassword!@#",
        }

        response = await async_client.post("/auth/login", json=payload)
        assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, async_client: AsyncClient):
        """Test login with missing fields fails."""
        # Missing password
        payload = {"email": "test@example.com"}
        response = await async_client.post("/auth/login", json=payload)
        assert response.status_code == 422  # Validation error


@pytest.mark.unit
@pytest.mark.api
class TestAuthUsers:
    """Tests for users list endpoint (admin only)."""

    @pytest.fixture
    async def admin_headers(self, async_client: AsyncClient, async_session):
        """Create an admin user and return auth headers."""
        from src.database.models import User
        from src.utils.security import hash_password

        # Create admin user directly in DB
        admin = User(
            email="admin_test@example.com",
            password_hash=hash_password("Test1234!@#"),
            name="Admin User",
            phone="01012345678",
            role="admin",
        )
        async_session.add(admin)
        await async_session.commit()

        # Login to get token
        response = await async_client.post(
            "/auth/login",
            json={"email": "admin_test@example.com", "password": "Test1234!@#"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def user_headers(self, async_client: AsyncClient):
        """Create a regular user and return auth headers."""
        payload = {
            "email": "regular_user@example.com",
            "password": "Test1234!@#",
            "password_confirm": "Test1234!@#",
            "name": "Regular User",
            "phone": "01012345678",
        }
        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_get_users_as_admin(self, async_client: AsyncClient, admin_headers):
        """Test getting users list as admin succeeds."""
        response = await async_client.get("/auth/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)

    @pytest.mark.asyncio
    async def test_get_users_as_regular_user(self, async_client: AsyncClient, user_headers):
        """Test getting users list as regular user fails."""
        response = await async_client.get("/auth/users", headers=user_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_users_no_auth(self, async_client: AsyncClient):
        """Test getting users list without authentication fails."""
        response = await async_client.get("/auth/users")
        assert response.status_code in [401, 403]


@pytest.mark.unit
@pytest.mark.api
class TestAuthChangePassword:
    """Tests for password change endpoint."""

    @pytest.fixture
    async def auth_user(self, async_client: AsyncClient):
        """Create a user and return user info with auth headers."""
        payload = {
            "email": "password_change@example.com",
            "password": "OldPassword!@#1",
            "password_confirm": "OldPassword!@#1",
            "name": "Password Test User",
            "phone": "01012345678",
        }
        response = await async_client.post("/auth/register", json=payload)
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {
            "headers": {"Authorization": f"Bearer {token}"},
            "old_password": payload["password"],
        }

    @pytest.mark.asyncio
    async def test_change_password_success(self, async_client: AsyncClient, auth_user):
        """Test successful password change."""
        payload = {
            "current_password": auth_user["old_password"],
            "new_password": "NewPassword!@#2",
            "new_password_confirm": "NewPassword!@#2",
        }

        response = await async_client.post(
            "/auth/change-password",
            json=payload,
            headers=auth_user["headers"],
        )

        assert response.status_code == 200

        # Verify can login with new password
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": "password_change@example.com",
                "password": "NewPassword!@#2",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, async_client: AsyncClient, auth_user):
        """Test password change with wrong current password fails."""
        payload = {
            "current_password": "WrongCurrentPassword!@#",
            "new_password": "NewPassword!@#2",
            "new_password_confirm": "NewPassword!@#2",
        }

        response = await async_client.post(
            "/auth/change-password",
            json=payload,
            headers=auth_user["headers"],
        )

        assert response.status_code == 401  # Unauthorized
