# tests/test_user_crud.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.crud.user import get_user_by_email, create_user

# ------------------ Tests for get_user_by_email ------------------

@pytest.mark.asyncio
async def test_get_user_by_email_found():
    # Create a fake User instance.
    fake_user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=False
    )

    # Build a fake result chain so that:
    # db.execute(...).scalars().first() returns fake_user.
    fake_scalars = MagicMock()
    fake_scalars.first.return_value = fake_user

    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    # Create a fake async database session.
    fake_db = MagicMock(spec=AsyncSession)
    fake_db.execute = AsyncMock(return_value=fake_result)

    # Call the function under test.
    result = await get_user_by_email(fake_db, "test@example.com")

    # Assert that the user is found.
    assert result == fake_user


@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    # Build a fake result chain returning None.
    fake_scalars = MagicMock()
    fake_scalars.first.return_value = None

    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    fake_db = MagicMock(spec=AsyncSession)
    fake_db.execute = AsyncMock(return_value=fake_result)

    result = await get_user_by_email(fake_db, "nonexistent@example.com")
    assert result is None

# ------------------ Tests for create_user ------------------

@pytest.mark.asyncio
async def test_create_user():
    # Create a UserCreate instance.
    user_create = UserCreate(
        email="newuser@example.com",
        password="secret"
    )
    
    # Create a fake async database session with the necessary methods.
    fake_db = MagicMock(spec=AsyncSession)
    fake_db.add = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    # Patch the get_password_hash function so that it returns a known value.
    with patch("app.crud.user.get_password_hash", return_value="fakehashed"):
        result = await create_user(fake_db, user_create)

    # Verify that the database methods were called.
    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited()
    fake_db.refresh.assert_awaited()

    # Check that the returned user has the expected data.
    assert result.email == user_create.email
    assert result.hashed_password == "fakehashed"
