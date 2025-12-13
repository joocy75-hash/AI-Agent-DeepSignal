#!/usr/bin/env python3
"""
Initialize admin account after database migration.

This script creates a default admin account if it doesn't exist.
Run this after alembic migrations are complete.

Usage:
    python scripts/init_admin.py

Environment Variables:
    ADMIN_EMAIL: Admin email (default: admin@admin.com)
    ADMIN_INITIAL_PASSWORD: Admin password (if not set, generates random)
"""
import asyncio
import os
import secrets
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import User
from src.utils.jwt_auth import JWTAuth


async def create_admin_user():
    """Create default admin user if not exists."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get admin credentials from environment variables
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@admin.com")
        admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")

        # Generate random password if not provided
        generated_password = None
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            generated_password = admin_password
            print("⚠️  ADMIN_INITIAL_PASSWORD not set in environment")
            print(f"⚠️  Generated random admin password: {admin_password}")
            print(f"⚠️  Please save this password securely!")

        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.email == admin_email)
        )
        existing_admin = result.scalars().first()

        if existing_admin:
            print(f"Admin user already exists (email: {admin_email}). Skipping creation.")
            return

        # Create admin user
        hashed_password = JWTAuth.get_password_hash(admin_password)
        admin_user = User(
            email=admin_email,
            password_hash=hashed_password,
            name="Administrator",
            role="admin",
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()
        print("✅ Admin user created successfully!")
        print(f"  Email: {admin_email}")
        if generated_password:
            print(f"  Password: {generated_password}")
            print("  ⚠️  IMPORTANT: Save this password! It won't be shown again.")
        else:
            print("  Password: (from ADMIN_INITIAL_PASSWORD env var)")
        print("  IMPORTANT: Change this password after first login!")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
