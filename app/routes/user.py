import os
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.schemas.user import UserCreate, UserOut, Token
from app.crud.user import get_user_by_email, create_user
from app.core.auth import create_access_token, verify_password
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
import cloudinary
import cloudinary.uploader

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
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=409, detail="User with this email already exists"
        )
    new_user = await create_user(db, user)
    return new_user


@router.post("/auth/login", response_model=Token)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.get("/auth/me", response_model=UserOut)
async def read_users_me(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):

    from app.core.auth import decode_access_token

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload["sub"]
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/auth/avatar", response_model=UserOut)
async def update_avatar(
    token: str = Depends(oauth2_scheme),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):

    from app.core.auth import decode_access_token

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload["sub"]

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = cloudinary.uploader.upload(file.file, folder="avatars")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Avatar upload failed: {str(e)}")

    user.avatar_url = result.get("secure_url")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
