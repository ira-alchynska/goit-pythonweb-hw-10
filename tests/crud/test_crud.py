# test_get_contact.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime, timedelta

from app.crud.crud import (
    get_contact,
    get_contacts,
    create_contact,
    update_contact,
    delete_contact,
    search_contacts,
    get_contacts_with_upcoming_birthdays
)
from app.models.models import Contact
from app.schemas.schemas import ContactCreate, ContactUpdate

# --- Helper: A fake Contact instance used across tests ---
fake_contact = Contact(
    id=1,
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    phone="123456789",
    birthday=date(1990, 1, 1),
    additional_data="Additional info"
) # Assuming Contact is defined in app/models.py

@pytest.mark.asyncio
async def test_get_contact_found():
    # Create a fake result chain for `db.execute`:
    # result.scalars().first() should return fake_contact.
    fake_scalars = MagicMock()
    fake_scalars.first.return_value = fake_contact

    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    # Create a fake asynchronous database session.
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    # Call the function under test.
    result = await get_contact(fake_db, contact_id=1)

    # Assert the returned contact matches the fake contact.
    assert result == fake_contact


@pytest.mark.asyncio
async def test_get_contact_not_found():
    # Set up the fake result chain such that no contact is found (first() returns None).
    fake_scalars = MagicMock()
    fake_scalars.first.return_value = None

    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    # Create a fake asynchronous database session.
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    # Call the function under test with a contact_id that does not exist.
    result = await get_contact(fake_db, contact_id=999)

    # Assert the function returns None when no contact is found.
    assert result is None

    # test_crud.py


# ---------- Test for get_contacts ----------
@pytest.mark.asyncio
async def test_get_contacts():
    # Create a fake result chain: result.scalars().all() returns a list of contacts.
    fake_contacts = [fake_contact]
    fake_scalars = MagicMock()
    fake_scalars.all.return_value = fake_contacts
    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    result = await get_contacts(fake_db, skip=0, limit=100)
    assert result == fake_contacts

# ---------- Test for create_contact ----------
@pytest.mark.asyncio
async def test_create_contact():
    # Create a ContactCreate instance.
    contact_create = ContactCreate(
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        phone="987654321",
        birthday=date(1985, 5, 15),
        additional_data="Data"
    )
    # Simulate the asynchronous db session methods.
    fake_db = MagicMock()
    fake_db.add = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock(return_value=None)

    # Call the create_contact function.
    result = await create_contact(fake_db, contact_create)
    
    # Validate that the created contact's data matches the input.
    assert result.first_name == contact_create.first_name
    assert result.last_name == contact_create.last_name
    assert result.email == contact_create.email
    
    # Ensure the db session methods were called.
    fake_db.add.assert_called_once()  
    fake_db.commit.assert_awaited()
    fake_db.refresh.assert_awaited()

# ---------- Test for update_contact ----------
@pytest.mark.asyncio
async def test_update_contact():
    contact_update = ContactUpdate(first_name="Updated")

    fake_db = MagicMock()
    fake_db.add = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock(return_value=None)

    fake_scalars = MagicMock()
    fake_scalars.first.return_value = fake_contact
    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars
    fake_db.execute = AsyncMock(return_value=fake_result)

    result = await update_contact(fake_db, contact_id=1, contact_update=contact_update)
    assert result.first_name == "Updated"
    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited()
    fake_db.refresh.assert_awaited()


# ---------- Test for delete_contact ----------
@pytest.mark.asyncio
async def test_delete_contact():
    fake_db = MagicMock()
    fake_db.delete = AsyncMock()
    fake_db.commit = AsyncMock()

    fake_scalars = MagicMock()
    fake_scalars.first.return_value = fake_contact
    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars
    fake_db.execute = AsyncMock(return_value=fake_result)

    result = await delete_contact(fake_db, contact_id=1)
    assert result == fake_contact
    fake_db.delete.assert_awaited_with(fake_contact)
    fake_db.commit.assert_awaited()

@pytest.mark.asyncio
async def test_update_contact2():
    contact_update = ContactUpdate(first_name="Updated")

    fake_db = MagicMock()
    fake_db.add = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock(return_value=None)

    # Use new_callable so that the patch automatically creates an AsyncMock.
    with patch('app.crud.crud.get_contact', new_callable=AsyncMock, return_value=fake_contact):
        result = await update_contact(fake_db, contact_id=1, contact_update=contact_update)
        assert result.first_name == "Updated"
        fake_db.add.assert_called_once()
        fake_db.commit.assert_awaited()
        fake_db.refresh.assert_awaited()

# ------------------ Test for delete_contact ------------------
@pytest.mark.asyncio
async def test_delete_contact2():
    fake_db = MagicMock()
    fake_db.delete = AsyncMock()
    fake_db.commit = AsyncMock()

    # Use new_callable to ensure get_contact is an AsyncMock.
    with patch('app.crud.crud.get_contact', new_callable=AsyncMock, return_value=fake_contact):
        result = await delete_contact(fake_db, contact_id=1)
        assert result == fake_contact
        fake_db.delete.assert_awaited_with(fake_contact)
        fake_db.commit.assert_awaited()

# ---------- Test for search_contacts ----------
@pytest.mark.asyncio
async def test_search_contacts():
    fake_contacts = [fake_contact]
    fake_scalars = MagicMock()
    fake_scalars.all.return_value = fake_contacts
    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    # Test search by first_name (similar tests can be done for last_name or email).
    result = await search_contacts(fake_db, first_name="John")
    assert result == fake_contacts

# ---------- Test for get_contacts_with_upcoming_birthdays ----------
@pytest.mark.asyncio
async def test_get_contacts_with_upcoming_birthdays():
    # Create a contact with a birthday in the next 7 days.
    today = datetime.today().date()
    upcoming_birthday = today + timedelta(days=3)
    contact_with_birthday = Contact(
        id=2,
        first_name="Birthday",
        last_name="Test",
        email="birthday.test@example.com",
        phone="000111222",
        birthday=upcoming_birthday,
        additional_data="Upcoming"
    )
    fake_contacts = [contact_with_birthday]
    fake_scalars = MagicMock()
    fake_scalars.all.return_value = fake_contacts
    fake_result = MagicMock()
    fake_result.scalars.return_value = fake_scalars

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    result = await get_contacts_with_upcoming_birthdays(fake_db)
    assert result == fake_contacts

