import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.auth import get_password_hash
from typing import Optional
from redis.asyncio import Redis

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

async def get_user_by_email_from_redis(redis: Redis, email: str) -> Optional[User]:
    """
    Retrieve a user by email from Redis.

    Args:
        redis (Redis): The asynchronous Redis connection.
        email (str): The email address of the user to retrieve.

    Returns:
        User: The user object if found; otherwise, None.
    """
    user_key = f"user:{email}"
    
    user_json = await redis.get(user_key)
    if user_json is None:
        return None

    user_data = json.loads(user_json)
    
    return User(**user_data)    


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

async def store_in_redis(redis: Redis, user: User):
    """
    Store a user object in Redis.

    Args:
        redis (Redis): The asynchronous Redis connection.
        user (User): The user object to store in Redis.

    Returns:
        None
    """
    user_data = {
        "id": user.id,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "is_active": bool(user.is_active),
        "is_verified": bool(user.is_verified),
        "avatar_url": user.avatar_url,
        "role": user.role
    }
    
    user_data_json = json.dumps(user_data)

    user_key = f"user:{user.email}"
    await redis.set(user_key, user_data_json, ex=3600)
