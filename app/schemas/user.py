from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    """
    Base schema for user-related data.

    Attributes:
        email (EmailStr): The email address of the user.
    """
    email: EmailStr


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Attributes:
        password (str): The password for the user.
    """
    password: str


class UserOut(UserBase):
    """
    Schema for outputting user data.

    Attributes:
        id (int): The unique identifier of the user.
        is_active (bool): Indicates if the user is active.
        is_verified (bool): Indicates if the user is verified.
        avatar_url (Optional[str]): The URL of the user's avatar (if any).
        role (str): The role of the user (e.g., admin, user).
    """
    id: int
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    """
    Schema for authentication tokens.

    Attributes:
        access_token (str): The access token string.
        token_type (str): The type of the token (e.g., Bearer).
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema for token data.

    Attributes:
        email (Optional[EmailStr]): The email address associated with the token (if any).
    """
    email: EmailStr | None = None
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str = Field(..., example="reset-token")
    new_password: str = Field(..., min_length=8)

class Message(BaseModel):
    message: str
