import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.auth import get_password_hash

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str):
    """
    Retrieve a user by email from the database.

    Args:
        db (AsyncSession): The asynchronous database session.
        email (str): The email address of the user to retrieve.

    Returns:
        User: The user object if found; otherwise, None.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate):
    """
    Create a new user in the database.

    Args:
        db (AsyncSession): The asynchronous database session.
        user (UserCreate): The user data for creating a new user.

    Returns:
        User: The created user object.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"Created user: {db_user.email}")
    return db_user
