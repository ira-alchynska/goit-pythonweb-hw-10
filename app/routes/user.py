"""
This module defines the API routes for user authentication and profile management.

Routes:
    - POST /auth/register: Registers a new user.
    - POST /auth/login: Authenticates a user and returns an access token.
    - GET /auth/me: Retrieves the authenticated user's profile.
    - POST /auth/avatar: Updates the authenticated user's avatar.
    - POST /auth/request-password-reset: Requests a password reset link.
    - POST /auth/reset-password: Resets the user's password.

Dependencies:
    - get_db: Provides a database session for route handlers.
    - oauth2_scheme: Handles OAuth2 token authentication.
"""

import os
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.schemas.user import UserCreate, UserOut, Token, PasswordResetRequest, PasswordReset, Message
from app.crud.user import get_user_by_email, create_user, get_user_by_email_from_redis, store_in_redis
from app.core.auth import create_access_token, verify_password, generate_reset_token, verify_reset_token, update_user_password
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from app.core.redis import get_redis
from redis.asyncio import Redis
import cloudinary
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


async def get_db():
    async with async_session() as session:
        yield session


@router.post("/auth/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user.

    Args:
        user (UserCreate): The user data for registration.
        db (AsyncSession): The database session.

    Returns:
        UserOut: The newly created user.

    Raises:
        HTTPException: If a user with the given email already exists.
    """
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=409, detail="User with this email already exists"
        )
    new_user = await create_user(db, user)
    return new_user

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Authenticates a user and returns an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): The login credentials.
        db (AsyncSession): The database session.
        redis (Redis): The Redis client.

    Returns:
        Token: The access token and token type.

    Raises:
        HTTPException: If the credentials are invalid.
    """
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})

    await store_in_redis(redis, user)
    
    return {"access_token": access_token, "token_type": "bearer"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.get("/auth/me", response_model=UserOut)
async def read_users_me(
    token: str = Depends(oauth2_scheme), redis: Redis = Depends(get_redis)
):
    """
    Retrieves the authenticated user's profile.

    Args:
        token (str): The OAuth2 token.
        redis (Redis): The Redis client.

    Returns:
        UserOut: The authenticated user's profile.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    from app.core.auth import decode_access_token

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload["sub"]
    user = await get_user_by_email_from_redis(redis, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/auth/avatar", response_model=UserOut)
async def update_avatar(
    token: str = Depends(oauth2_scheme),
    email: str = None,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Updates the authenticated user's avatar.

    Args:
        token (str): The OAuth2 token.
        email (str, optional): The user's email. Defaults to None.
        file (UploadFile): The avatar file to upload.
        db (AsyncSession): The database session.
        redis (Redis): The Redis client.

    Returns:
        UserOut: The updated user profile.

    Raises:
        HTTPException: If the token is invalid, the user is not found, or the upload fails.
    """
    from app.core.auth import decode_access_token

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    emailSub = payload["sub"]

    user_email = email or emailSub

    userLoggedIn = await get_user_by_email_from_redis(redis, emailSub)
    user = await get_user_by_email(db, user_email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not userLoggedIn.role == "admin":
        raise HTTPException(status_code=403, detail="Only admins are allowed to update avatar")

    try:
        result = cloudinary.uploader.upload(file.file, folder="avatars")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Avatar upload failed: {str(e)}")

    user.avatar_url = result.get("secure_url")
    await db.commit()
    await db.refresh(user)
    await store_in_redis(redis, user)
    return user

@router.post("/auth/request-password-reset", response_model=Message)
async def request_password_reset(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """
    Requests a password reset link.

    Args:
        request (PasswordResetRequest): The password reset request data.
        db (AsyncSession): The database session.

    Returns:
        Message: A message indicating whether the reset link was sent.
    """
    user = await get_user_by_email(db, request.email)
    if not user:
        return Message(message="If the email exists, a reset link has been sent.")
    
    reset_token = generate_reset_token(request.email)
    
    print(f"Password reset token for {request.email}: {reset_token}")
    return Message(message="If the email exists, a reset link has been sent.")

@router.post("/auth/reset-password", response_model=Message)
async def reset_password(reset: PasswordReset, db: AsyncSession = Depends(get_db)):
    """
    Resets the user's password.

    Args:
        reset (PasswordReset): The password reset data.
        db (AsyncSession): The database session.

    Returns:
        Message: A message indicating the password reset was successful.
    """
    email = verify_reset_token(reset.token)
    
    await update_user_password(db, email, reset.new_password)
    
    return Message(message="Password has been reset successfully.")

app = FastAPI()
app.include_router(router)
