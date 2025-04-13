from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.user import User
from app.routes.user import app

client = TestClient(app)

fake_user_obj = User(
    id=1,
    email="user@example.com",
    hashed_password="fakehashed",
    role="user",
    is_active=True,
    is_verified=False,
    avatar_url=None
)

fake_admin_user_obj = User(
    id=2,
    email="admin@example.com",
    hashed_password="fakehashed",
    role="admin",
    is_active=True,
    is_verified=False,
    avatar_url=None
)

dummy_db = AsyncMock()
dummy_db.add = MagicMock()
dummy_db.commit = AsyncMock()
dummy_db.refresh = AsyncMock()

async def override_get_db():
    yield dummy_db

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
        "username": "user@example.com",
        "password": "correctpassword"
    }
    with patch("app.routes.user.get_user_by_email", new=AsyncMock(return_value=fake_user_obj)):
        with patch("app.routes.user.verify_password", return_value=True):
            with patch("app.routes.user.create_access_token", return_value="faketoken"):
                with patch("app.routes.user.store_in_redis", new=AsyncMock(return_value=None)):
                    response = client.post("/auth/login", data=form_data)
                    assert response.status_code == 200, response.text
                    data = response.json()
                    assert data["access_token"] == "faketoken"
                    assert data["token_type"] == "bearer"

def test_login_failure_invalid_credentials():
    form_data = {
        "username": "user@example.com",
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
        with patch("app.routes.user.get_user_by_email_from_redis", new=AsyncMock(return_value=fake_user_obj)):
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
        assert response.status_code == 401, response.textpy
