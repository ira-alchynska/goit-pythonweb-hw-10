from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.crud import crud
from app.routes.routes import app

client = TestClient(app)

fake_contact = {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "123456789",
    "birthday": "1990-01-01",
    "additional_data": "Additional info"
}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "Welcome to the Contacts API"}

def test_create_contact():
    new_contact_payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "987654321",
        "birthday": "1992-02-02",
        "additional_data": "New contact"
    }

    with patch.object(crud, "create_contact", new=AsyncMock(return_value=fake_contact)):
        response = client.post("/contacts/", json=new_contact_payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == fake_contact["id"]
        assert data["email"] == fake_contact["email"]

def test_read_contacts_list():
    with patch.object(crud, "get_contacts", new=AsyncMock(return_value=[fake_contact])):
        response = client.get("/contacts/?skip=0&limit=100")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == fake_contact["id"]

def test_read_contacts_search():
    with patch.object(crud, "search_contacts", new=AsyncMock(return_value=[fake_contact])):
        response = client.get("/contacts/?first_name=John")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == fake_contact["first_name"]

def test_read_contact_found():
    with patch.object(crud, "get_contact", new=AsyncMock(return_value=fake_contact)):
        response = client.get("/contacts/1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == fake_contact["id"]

def test_read_contact_not_found():
    with patch.object(crud, "get_contact", new=AsyncMock(return_value=None)):
        response = client.get("/contacts/999")
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"

def test_update_contact_found():
    updated_contact = fake_contact.copy()
    updated_contact["first_name"] = "UpdatedName"

    with patch.object(crud, "update_contact", new=AsyncMock(return_value=updated_contact)):
        update_payload = {"first_name": "UpdatedName"}
        response = client.put("/contacts/1", json=update_payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == "UpdatedName"

def test_update_contact_not_found():
    with patch.object(crud, "update_contact", new=AsyncMock(return_value=None)):
        update_payload = {"first_name": "UpdatedName"}
        response = client.put("/contacts/999", json=update_payload)
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"

def test_delete_contact_found():
    with patch.object(crud, "delete_contact", new=AsyncMock(return_value=fake_contact)):
        response = client.delete("/contacts/1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == fake_contact["id"]

def test_delete_contact_not_found():
    with patch.object(crud, "delete_contact", new=AsyncMock(return_value=None)):
        response = client.delete("/contacts/999")
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"

def test_upcoming_birthdays():
    with patch.object(crud, "get_contacts_with_upcoming_birthdays", new=AsyncMock(return_value=[fake_contact])):
        response = client.get("/contacts/birthdays/upcoming")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == fake_contact["id"]
