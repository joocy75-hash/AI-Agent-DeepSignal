#!/usr/bin/env python3
"""
API 키 연결 테스트 스크립트
사용자의 Bitget API 키가 제대로 작동하는지 직접 테스트합니다.
"""

import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import ApiKey, User
from utils.crypto_secrets import decrypt_secret
from services.exchanges import exchange_manager

async def test_api_connection(user_id: int = 6):
    """Test API connection for a specific user"""

    # Database connection
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trading.db")
    engine = create_async_engine(db_url)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Get user
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalars().first()

        if not user:
            print(f"❌ User {user_id} not found")
            return

        print(f"✅ Found user: {user.email}")
        print(f"   Exchange: {user.exchange}")

        # Get API keys
        api_key_result = await session.execute(
            select(ApiKey).where(ApiKey.user_id == user_id)
        )
        api_key = api_key_result.scalars().first()

        if not api_key:
            print(f"❌ No API keys configured for user {user_id}")
            return

        print(f"✅ API keys found")

        # Decrypt keys
        try:
            decrypted_api = decrypt_secret(api_key.encrypted_api_key)
            decrypted_secret = decrypt_secret(api_key.encrypted_secret_key)
            decrypted_passphrase = decrypt_secret(api_key.encrypted_passphrase) if api_key.encrypted_passphrase else ""

            print(f"✅ Keys decrypted successfully")
            print(f"   API Key: {decrypted_api[:10]}...{decrypted_api[-10:]}")
            print(f"   Secret: {decrypted_secret[:10]}...{decrypted_secret[-10:]}")
            if decrypted_passphrase:
                print(f"   Passphrase: {decrypted_passphrase[:5]}...")

        except Exception as e:
            print(f"❌ Failed to decrypt keys: {e}")
            return

        # Test exchange connection
        exchange_name = user.exchange or "bitget"
        print(f"\n🔄 Testing {exchange_name} API connection...")

        try:
            # Create exchange client
            client = exchange_manager.get_client(
                user_id=user_id,
                exchange_name=exchange_name,
                api_key=decrypted_api,
                secret_key=decrypted_secret,
                passphrase=decrypted_passphrase if decrypted_passphrase else None
            )

            print(f"✅ Exchange client created")

            # Test balance API
            print(f"\n🔄 Testing balance API...")
            balance = await client.get_futures_balance()
            print(f"✅ Balance API working!")
            print(f"   Total: {balance.get('total', 0)} USDT")
            print(f"   Free: {balance.get('free', 0)} USDT")
            print(f"   Used: {balance.get('used', 0)} USDT")
            print(f"   Unrealized PNL: {balance.get('unrealized_pnl', 0)} USDT")

            # Test positions API
            print(f"\n🔄 Testing positions API...")
            positions = await client.get_positions()
            print(f"✅ Positions API working!")
            print(f"   Open positions: {len(positions)}")

            if positions:
                for pos in positions:
                    print(f"   - {pos.get('symbol')}: {pos.get('side')} {pos.get('size')} @ {pos.get('entry_price')}")

            print(f"\n🎉 All tests passed! API connection is working correctly.")

        except Exception as e:
            print(f"❌ Exchange API test failed: {e}")
            import traceback
            traceback.print_exc()
            return

    await engine.dispose()

if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    asyncio.run(test_api_connection(user_id))
