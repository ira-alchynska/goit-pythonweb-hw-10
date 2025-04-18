from sqlalchemy import Column, Integer, String, Boolean
from app.models.models import Base


class User(Base):
    """
    Represents a user entity in the database.

    Attributes:
        id (int): The primary key of the user.
        email (str): The unique email address of the user.
        hashed_password (str): The hashed password of the user.
        is_active (bool): Indicates if the user is active.
        is_verified (bool): Indicates if the user is verified.
        avatar_url (str): The URL of the user's avatar (if any).
        role (str): The role of the user (e.g., admin, user).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)
