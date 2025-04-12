# tests/test_routes.py
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import the app instance and the crud module that gets patched.
from app.crud import crud  # The module that contains the CRUD functions
from app.routes.routes import app  # The FastAPI app created in your router file

# Create a TestClient instance for synchronous testing of async endpoints.
client = TestClient(app)

# A fake contact object (as a dict) that matches the response_model schema.
fake_contact = {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "123456789",
    "birthday": "1990-01-01",
    "additional_data": "Additional info"
}

# ----------------- Test GET "/" - the root endpoint -----------------

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "Welcome to the Contacts API"}


# ----------------- Test POST /contacts/ -----------------

def test_create_contact():
    # Prepare a contact payload (for creation)
    new_contact_payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "987654321",
        "birthday": "1992-02-02",
        "additional_data": "New contact"
    }

    # Patch the crud.create_contact so that it returns a fake contact.
    with patch.object(crud, "create_contact", new=AsyncMock(return_value=fake_contact)):
        response = client.post("/contacts/", json=new_contact_payload)
        assert response.status_code == 200, response.text
        data = response.json()
        # Verify the returned JSON contains expected fake contact fields.
        assert data["id"] == fake_contact["id"]
        assert data["email"] == fake_contact["email"]


# ----------------- Test GET /contacts/ for listing all contacts -----------------

def test_read_contacts_list():
    # Test retrieving list without search filters.
    with patch.object(crud, "get_contacts", new=AsyncMock(return_value=[fake_contact])):
        response = client.get("/contacts/?skip=0&limit=100")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == fake_contact["id"]

def test_read_contacts_search():
    # Test retrieving contacts with search filters.
    with patch.object(crud, "search_contacts", new=AsyncMock(return_value=[fake_contact])):
        response = client.get("/contacts/?first_name=John")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == fake_contact["first_name"]


# ----------------- Test GET /contacts/{contact_id} -----------------

def test_read_contact_found():
    # Patch get_contact to return our fake contact.
    with patch.object(crud, "get_contact", new=AsyncMock(return_value=fake_contact)):
        response = client.get("/contacts/1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == fake_contact["id"]

def test_read_contact_not_found():
    # Patch get_contact to return None so that 404 is raised.
    with patch.object(crud, "get_contact", new=AsyncMock(return_value=None)):
        response = client.get("/contacts/999")
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"


# ----------------- Test PUT /contacts/{contact_id} -----------------

def test_update_contact_found():
    # Assume an updated fake contact (e.g., first_name changed)
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


# ----------------- Test DELETE /contacts/{contact_id} -----------------

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


# ----------------- Test GET /contacts/birthdays/upcoming -----------------

def test_upcoming_birthdays():
    # Return a list with one fake contact.
    with patch.object(crud, "get_contacts_with_upcoming_birthdays", new=AsyncMock(return_value=[fake_contact])):
        response = client.get("/contacts/birthdays/upcoming")
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == fake_contact["id"]
