"""
Unit tests for crypto_secrets module (API key encryption/decryption).
"""
import pytest
import os
from cryptography.fernet import Fernet

from src.utils.crypto_secrets import (
    encrypt_secret,
    decrypt_secret,
    get_fernet,
    CryptoError,
)


@pytest.fixture(scope="module")
def setup_encryption_key():
    """
    Ensure ENCRYPTION_KEY is set for testing.
    """
    original_key = os.getenv("ENCRYPTION_KEY")

    # Generate a test key
    test_key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = test_key

    yield test_key

    # Restore original key
    if original_key:
        os.environ["ENCRYPTION_KEY"] = original_key
    else:
        os.environ.pop("ENCRYPTION_KEY", None)


@pytest.mark.unit
class TestCryptoSecrets:
    """Tests for encryption/decryption functions."""

    def test_encrypt_and_decrypt_simple_string(self, setup_encryption_key):
        """Test encrypting and decrypting a simple string."""
        plaintext = "my-secret-api-key"

        # Encrypt
        ciphertext = encrypt_secret(plaintext)
        assert ciphertext != plaintext
        assert len(ciphertext) > 0

        # Decrypt
        decrypted = decrypt_secret(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_and_decrypt_special_characters(self, setup_encryption_key):
        """Test encrypting strings with special characters."""
        plaintext = "abc123!@#$%^&*()_+-={}[]|\\:\";<>?,./"

        ciphertext = encrypt_secret(plaintext)
        decrypted = decrypt_secret(ciphertext)

        assert decrypted == plaintext

    def test_encrypt_and_decrypt_unicode(self, setup_encryption_key):
        """Test encrypting Unicode characters."""
        plaintext = "안녕하세요 🔐 Ключ секрет"

        ciphertext = encrypt_secret(plaintext)
        decrypted = decrypt_secret(ciphertext)

        assert decrypted == plaintext

    def test_encrypt_none_returns_empty_string(self, setup_encryption_key):
        """Test that encrypting None returns empty string."""
        result = encrypt_secret(None)
        assert result == ""

    def test_decrypt_none_returns_none(self, setup_encryption_key):
        """Test that decrypting None returns None."""
        result = decrypt_secret(None)
        assert result is None

    def test_decrypt_empty_string_returns_none(self, setup_encryption_key):
        """Test that decrypting empty string returns None."""
        result = decrypt_secret("")
        assert result is None

    def test_decrypt_invalid_token_raises_error(self, setup_encryption_key):
        """Test that decrypting invalid token raises CryptoError."""
        with pytest.raises(CryptoError, match="Cannot decrypt secret"):
            decrypt_secret("invalid-token-that-is-not-encrypted")

    def test_get_fernet_returns_fernet_instance(self, setup_encryption_key):
        """Test that get_fernet returns a Fernet instance."""
        fernet = get_fernet()
        assert isinstance(fernet, Fernet)

    def test_encrypted_data_is_different_each_time(self, setup_encryption_key):
        """Test that same plaintext encrypts to different ciphertext each time."""
        plaintext = "same-secret"

        ciphertext1 = encrypt_secret(plaintext)
        ciphertext2 = encrypt_secret(plaintext)

        # Ciphertext should be different (Fernet adds random IV)
        assert ciphertext1 != ciphertext2

        # But both should decrypt to same plaintext
        assert decrypt_secret(ciphertext1) == plaintext
        assert decrypt_secret(ciphertext2) == plaintext

    def test_long_secret_encryption(self, setup_encryption_key):
        """Test encrypting very long secrets."""
        plaintext = "a" * 10000  # 10KB secret

        ciphertext = encrypt_secret(plaintext)
        decrypted = decrypt_secret(ciphertext)

        assert decrypted == plaintext
