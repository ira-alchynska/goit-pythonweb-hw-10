"""
This module defines the API routes for the Contacts application.

Routes:
    - GET /: Provides a welcome message.
    - POST /contacts/: Creates a new contact.
    - GET /contacts/: Retrieves a list of contacts with optional filters.
    - GET /contacts/{contact_id}: Retrieves a specific contact by ID.
    - PUT /contacts/{contact_id}: Updates a specific contact by ID.
    - DELETE /contacts/{contact_id}: Deletes a specific contact by ID.
    - GET /contacts/birthdays/upcoming: Retrieves contacts with upcoming birthdays.

Dependencies:
    - get_db: Provides a database session for route handlers.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core import database
from app.crud import crud
from app.schemas import schemas

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency to get the database session
async def get_db():
    async with database.async_session() as session:
        yield session


@router.get("/")
async def read_root():
    """
    Root endpoint to provide a welcome message.

    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to the Contacts API"}


@router.post("/contacts/", response_model=schemas.Contact)
async def create_contact(
    contact: schemas.ContactCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new contact.

    Args:
        contact (schemas.ContactCreate): The contact data to create.
        db (AsyncSession): The database session.

    Returns:
        schemas.Contact: The created contact.
    """
    logger.info("Received request to create contact: %s", contact)
    db_contact = await crud.create_contact(db, contact)
    return db_contact


@router.get("/contacts/", response_model=list[schemas.Contact])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    first_name: str = Query(None),
    last_name: str = Query(None),
    email: str = Query(None),
):
    """
    Retrieve a list of contacts with optional filters.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        db (AsyncSession): The database session.
        first_name (str): Filter by first name.
        last_name (str): Filter by last name.
        email (str): Filter by email.

    Returns:
        list[schemas.Contact]: A list of contacts.
    """
    if first_name or last_name or email:
        contacts = await crud.search_contacts(db, first_name, last_name, email)
    else:
        contacts = await crud.get_contacts(db, skip, limit)
    logger.info("Fetched contacts: %s", contacts)
    return contacts


@router.get("/contacts/{contact_id}", response_model=schemas.Contact)
async def read_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        db (AsyncSession): The database session.

    Returns:
        schemas.Contact: The retrieved contact.
    """
    contact = await crud.get_contact(db, contact_id)
    if contact is None:
        logger.warning("Contact not found: %s", contact_id)
        raise HTTPException(status_code=404, detail="Contact not found")
    logger.info("Fetched contact: %s", contact)
    return contact


@router.put("/contacts/{contact_id}", response_model=schemas.Contact)
async def update_contact(
    contact_id: int, contact: schemas.ContactUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to update.
        contact (schemas.ContactUpdate): The updated contact data.
        db (AsyncSession): The database session.

    Returns:
        schemas.Contact: The updated contact.
    """
    updated = await crud.update_contact(db, contact_id, contact)
    if updated is None:
        logger.warning("Contact not found for update: %s", contact_id)
        raise HTTPException(status_code=404, detail="Contact not found")
    logger.info("Updated contact: %s", updated)
    return updated


@router.delete("/contacts/{contact_id}", response_model=schemas.Contact)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to delete.
        db (AsyncSession): The database session.

    Returns:
        schemas.Contact: The deleted contact.
    """
    deleted = await crud.delete_contact(db, contact_id)
    if deleted is None:
        logger.warning("Contact not found for deletion: %s", contact_id)
        raise HTTPException(status_code=404, detail="Contact not found")
    logger.info("Deleted contact: %s", deleted)
    return deleted


@router.get("/contacts/birthdays/upcoming", response_model=list[schemas.Contact])
async def upcoming_birthdays(db: AsyncSession = Depends(get_db)):
    """
    Retrieve contacts with upcoming birthdays.

    Args:
        db (AsyncSession): The database session.

    Returns:
        list[schemas.Contact]: A list of contacts with upcoming birthdays.
    """
    contacts = await crud.get_contacts_with_upcoming_birthdays(db)
    logger.info("Contacts with upcoming birthdays: %s", contacts)
    return contacts


# Create the FastAPI app and include the router
app = FastAPI()
app.include_router(router)
