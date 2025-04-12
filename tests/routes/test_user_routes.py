# tests/test_auth_routes.py
import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Import the FastAPI app with the routes.
from app.routes.user import app, get_db  # get_db is the dependency we’ll override

# Create a TestClient instance.
client = TestClient(app)

# A dummy user class to simulate a User ORM model.
class DummyUser:
    def __init__(self, id, email, hashed_password, is_active=True, is_verified=False, avatar_url=None):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.is_verified = is_verified
        self.avatar_url = avatar_url

# For endpoints that expect an object with attributes,
# use a DummyUser instance.
fake_user_obj = DummyUser(
    id=1,
    email="user@example.com",
    hashed_password="fakehashed",
    is_active=True,
    is_verified=False,
    avatar_url=None,
)

# For endpoints that return JSON via Pydantic conversion,
# you may still use a dict version.
fake_user_dict = {
    "id": 1,
    "email": "user@example.com",
    "hashed_password": "fakehashed",
    "is_active": True,
    "is_verified": False,
    "avatar_url": None,
}

#############################################
# Helper to override get_db dependency
#############################################

# Create a dummy DB session: a mock with AsyncMock methods for commit/refresh
dummy_db = AsyncMock()
dummy_db.add = MagicMock()          # add is normally a synchronous method
dummy_db.commit = AsyncMock()
dummy_db.refresh = AsyncMock()

async def override_get_db():
    yield dummy_db

#############################################
# Tests for POST /auth/register, /auth/login, /auth/me
# (these tests remain unchanged)
#############################################

def test_register_success():
    new_user_payload = {
        "email": "newuser@example.com",
        "password": "newpassword"
    }
    with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=None)):
        with patch("app.routes.user.create_user", new=AsyncMock(return_value=fake_user_obj)):
            response = client.post("/auth/register", json=new_user_payload)
            assert response.status_code == 201, response.text
            data = response.json()
            assert data["email"] == fake_user_obj.email

def test_register_existing():
    new_user_payload = {
        "email": "existing@example.com",
        "password": "password123"
    }
    with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=fake_user_obj)):
        response = client.post("/auth/register", json=new_user_payload)
        assert response.status_code == 409, response.text
        data = response.json()
        assert data["detail"] == "User with this email already exists"

def test_login_success():
    form_data = {
        "email": "user@example.com",
        "password": "correctpassword"
    }
    with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=fake_user_obj)):
        with patch("app.routes.user.verify_password", return_value=True):
            with patch("app.routes.user.create_access_token", return_value="faketoken"):
                response = client.post("/auth/login", data=form_data)
                assert response.status_code == 200, response.text
                data = response.json()
                assert data["access_token"] == "faketoken"
                assert data["token_type"] == "bearer"

def test_login_failure_invalid_credentials():
    form_data = {
        "email": "user@example.com",
        "password": "wrongpassword"
    }
    with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=None)):
        response = client.post("/auth/login", data=form_data)
        assert response.status_code == 401, response.text

    with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=fake_user_obj)):
        with patch("app.routes.user.verify_password", return_value=False):
            response = client.post("/auth/login", data=form_data)
            assert response.status_code == 401, response.text

def test_read_users_me_success():
    valid_token = "valid.token.here"
    payload = {"sub": "user@example.com"}
    with patch("app.core.auth.decode_access_token", return_value=payload):
        with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=fake_user_obj)):
            headers = {"Authorization": f"Bearer {valid_token}"}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["email"] == fake_user_obj.email

def test_read_users_me_invalid_token():
    invalid_token = "invalid.token"
    with patch("app.core.auth.decode_access_token", return_value=None):
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401, response.text

#############################################
# Tests for POST /auth/avatar
#############################################

def test_update_avatar_success():
    valid_token = "valid.token.here"
    payload = {"sub": "user@example.com"}
    # Use fake_user_obj (an instance of DummyUser with attributes) for avatar update.
    dummy_user = fake_user_obj
    # Simulate a successful Cloudinary upload.
    cloudinary_result = {"secure_url": "https://res.cloudinary.com/fakeimage.jpg"}

    # Override the get_db dependency to return our dummy_db session.
    app.dependency_overrides[get_db] = override_get_db

    with patch("app.core.auth.decode_access_token", return_value=payload):
        with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=dummy_user)):
            with patch("app.routes.user.cloudinary.uploader.upload", return_value=cloudinary_result):
                file_content = b"dummy image content"
                files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
                headers = {"Authorization": f"Bearer {valid_token}"}
                response = client.post("/auth/avatar", headers=headers, files=files)
                assert response.status_code == 200, response.text
                data = response.json()
                assert data["avatar_url"] == cloudinary_result["secure_url"]

    # Clear the override after the test.
    app.dependency_overrides.pop(get_db, None)

def test_update_avatar_upload_failure():
    valid_token = "valid.token.here"
    payload = {"sub": "user@example.com"}
    dummy_user = fake_user_obj

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.core.auth.decode_access_token", return_value=payload):
        with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=dummy_user)):
            with patch("app.routes.user.cloudinary.uploader.upload", side_effect=Exception("Upload error")):
                file_content = b"dummy image content"
                files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
                headers = {"Authorization": f"Bearer {valid_token}"}
                response = client.post("/auth/avatar", headers=headers, files=files)
                assert response.status_code == 500, response.text
                data = response.json()
                assert "Avatar upload failed" in data["detail"]

    app.dependency_overrides.pop(get_db, None)
