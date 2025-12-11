"""
Unit tests for JWT authentication utilities.
"""
import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException

from src.utils.jwt_auth import JWTAuth, TokenData
from src.config import settings


@pytest.mark.unit
class TestJWTAuth:
    """Tests for JWTAuth class."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "securepassword123"

        # Hash password
        hashed = JWTAuth.get_password_hash(password)

        # Verify hash is different from plaintext
        assert hashed != password
        assert len(hashed) > 0

        # Verify correct password
        assert JWTAuth.verify_password(password, hashed) is True

        # Verify wrong password
        assert JWTAuth.verify_password("wrongpassword", hashed) is False

    def test_password_hashing_different_each_time(self):
        """Test that same password hashes to different values (salt)."""
        password = "testpassword"

        hash1 = JWTAuth.get_password_hash(password)
        hash2 = JWTAuth.get_password_hash(password)

        # Different hashes
        assert hash1 != hash2

        # But both verify correctly
        assert JWTAuth.verify_password(password, hash1) is True
        assert JWTAuth.verify_password(password, hash2) is True

    def test_create_access_token_default_expiration(self):
        """Test creating access token with default expiration."""
        data = {"user_id": 1, "email": "test@example.com"}

        token = JWTAuth.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )

        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_create_access_token_custom_expiration(self):
        """Test creating access token with custom expiration."""
        data = {"user_id": 2, "email": "admin@example.com"}
        expires_delta = timedelta(hours=1)

        token = JWTAuth.create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )

        assert payload["user_id"] == 2
        assert "exp" in payload

    def test_decode_token_success(self):
        """Test decoding valid token."""
        data = {"user_id": 3, "email": "user@example.com"}
        token = JWTAuth.create_access_token(data)

        # Decode token
        payload = JWTAuth.decode_token(token)

        assert payload["user_id"] == 3
        assert payload["email"] == "user@example.com"

    def test_decode_token_invalid_raises_exception(self):
        """Test decoding invalid token raises HTTPException."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            JWTAuth.decode_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_token_expired_raises_exception(self):
        """Test decoding expired token raises HTTPException."""
        data = {"user_id": 4, "email": "expired@example.com"}
        # Create token that expires immediately
        token = JWTAuth.create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            JWTAuth.decode_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_token_wrong_secret_raises_exception(self):
        """Test decoding token with wrong secret raises HTTPException."""
        data = {"user_id": 5, "email": "wrong@example.com"}

        # Create token with different secret
        wrong_token = jwt.encode(
            data,
            "wrong-secret-key",
            algorithm=settings.jwt_algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            JWTAuth.decode_token(wrong_token)

        assert exc_info.value.status_code == 401


@pytest.mark.unit
class TestTokenData:
    """Tests for TokenData class."""

    def test_token_data_creation(self):
        """Test creating TokenData instance."""
        token_data = TokenData(user_id=1, email="test@example.com")

        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"

    def test_token_data_attributes(self):
        """Test TokenData attributes."""
        token_data = TokenData(user_id=42, email="admin@admin.com")

        assert hasattr(token_data, "user_id")
        assert hasattr(token_data, "email")
        assert isinstance(token_data.user_id, int)
        assert isinstance(token_data.email, str)
