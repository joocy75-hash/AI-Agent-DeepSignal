"""
Unit tests for ExchangeService (Phase 4).
"""
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from src.services.exchange_service import ExchangeService
from src.database.models import User, ApiKey
from src.utils.jwt_auth import JWTAuth


@pytest.mark.unit
@pytest.mark.database
class TestExchangeService:
    """Tests for ExchangeService."""

    @pytest.fixture
    async def test_user(self, async_session):
        """Create a test user."""
        user = User(
            email="test@example.com",
            password_hash=JWTAuth.get_password_hash("testpass"),
            role="user",
            exchange="bitget"
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    @pytest.fixture
    async def test_user_with_api_key(self, async_session, test_user):
        """Create a test user with API keys."""
        from src.utils.crypto_secrets import encrypt_secret

        api_key = ApiKey(
            user_id=test_user.id,
            encrypted_api_key=encrypt_secret("test-api-key"),
            encrypted_secret_key=encrypt_secret("test-secret-key"),
            encrypted_passphrase=encrypt_secret("test-passphrase")
        )
        async_session.add(api_key)
        await async_session.commit()
        await async_session.refresh(test_user)
        return test_user

    @pytest.mark.asyncio
    async def test_has_api_key_returns_true_when_exists(
        self,
        async_session,
        test_user_with_api_key
    ):
        """Test has_api_key returns True when API key exists."""
        result = await ExchangeService.has_api_key(
            async_session,
            test_user_with_api_key.id
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_has_api_key_returns_false_when_not_exists(
        self,
        async_session,
        test_user
    ):
        """Test has_api_key returns False when API key doesn't exist."""
        result = await ExchangeService.has_api_key(
            async_session,
            test_user.id
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_has_api_key_returns_false_for_nonexistent_user(
        self,
        async_session
    ):
        """Test has_api_key returns False for non-existent user."""
        result = await ExchangeService.has_api_key(
            async_session,
            user_id=99999  # Non-existent user
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_exchange_client_raises_when_no_api_key(
        self,
        async_session,
        test_user
    ):
        """Test get_user_exchange_client raises HTTPException when no API key."""
        with pytest.raises(HTTPException) as exc_info:
            await ExchangeService.get_user_exchange_client(
                async_session,
                test_user.id
            )

        assert exc_info.value.status_code == 400
        assert "API keys not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_exchange_client_success(
        self,
        async_session,
        test_user_with_api_key
    ):
        """Test get_user_exchange_client successfully creates client."""
        # Mock exchange_manager.get_client
        with patch("src.services.exchange_service.exchange_manager") as mock_manager:
            mock_client = AsyncMock()
            mock_manager.get_client.return_value = mock_client

            client, exchange_name = await ExchangeService.get_user_exchange_client(
                async_session,
                test_user_with_api_key.id
            )

            # Verify client and exchange name
            assert client == mock_client
            assert exchange_name == "bitget"

            # Verify get_client was called with correct arguments
            mock_manager.get_client.assert_called_once()
            call_kwargs = mock_manager.get_client.call_args[1]
            assert call_kwargs["user_id"] == test_user_with_api_key.id
            assert call_kwargs["exchange_name"] == "bitget"
            assert call_kwargs["api_key"] == "test-api-key"
            assert call_kwargs["secret_key"] == "test-secret-key"
            assert call_kwargs["passphrase"] == "test-passphrase"

    @pytest.mark.asyncio
    async def test_get_user_exchange_client_uses_default_exchange(
        self,
        async_session,
        test_user_with_api_key
    ):
        """Test get_user_exchange_client uses default exchange when user.exchange is None."""
        # Update user to have no exchange set
        test_user_with_api_key.exchange = None
        async_session.add(test_user_with_api_key)
        await async_session.commit()

        with patch("src.services.exchange_service.exchange_manager") as mock_manager:
            mock_client = AsyncMock()
            mock_manager.get_client.return_value = mock_client

            client, exchange_name = await ExchangeService.get_user_exchange_client(
                async_session,
                test_user_with_api_key.id
            )

            # Should use default exchange from config
            from src.config import ExchangeConfig
            assert exchange_name == ExchangeConfig.DEFAULT_EXCHANGE

    @pytest.mark.asyncio
    async def test_get_user_exchange_client_handles_exchange_error(
        self,
        async_session,
        test_user_with_api_key
    ):
        """Test get_user_exchange_client handles exchange connection errors."""
        # Mock exchange_manager to raise exception
        with patch("src.services.exchange_service.exchange_manager") as mock_manager:
            mock_manager.get_client.side_effect = Exception("Connection failed")

            with pytest.raises(HTTPException) as exc_info:
                await ExchangeService.get_user_exchange_client(
                    async_session,
                    test_user_with_api_key.id
                )

            assert exc_info.value.status_code == 500
            assert "Failed to connect to exchange" in exc_info.value.detail
