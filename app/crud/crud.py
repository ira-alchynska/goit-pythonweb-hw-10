import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Contact
from app.schemas.schemas import ContactCreate, ContactUpdate
from datetime import datetime, timedelta


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_contact(db: AsyncSession, contact_id: int):
    logger.info(f"Fetching contact with id: {contact_id}")
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalars().first()
    logger.info(f"Contact fetched: {contact}")
    return contact


async def get_contacts(db: AsyncSession, skip: int = 0, limit: int = 100):
    logger.info(f"Fetching contacts with skip: {skip}, limit: {limit}")
    result = await db.execute(select(Contact).offset(skip).limit(limit))
    contacts = result.scalars().all()
    logger.info(f"Contacts fetched: {contacts}")
    return contacts


async def create_contact(db: AsyncSession, contact: ContactCreate):
    logger.info(f"Creating contact: {contact}")
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    logger.info(f"Contact created: {db_contact}")
    return db_contact


async def update_contact(
    db: AsyncSession, contact_id: int, contact_update: ContactUpdate
):
    logger.info(f"Updating contact with id: {contact_id}")
    db_contact = await get_contact(db, contact_id)
    if not db_contact:
        logger.warning(f"Contact with id: {contact_id} not found")
        return None
    for var, value in contact_update.model_dump(exclude_unset=True).items():
        setattr(db_contact, var, value)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    logger.info(f"Contact updated: {db_contact}")
    return db_contact


async def delete_contact(db: AsyncSession, contact_id: int):
    logger.info(f"Deleting contact with id: {contact_id}")
    db_contact = await get_contact(db, contact_id)
    if not db_contact:
        logger.warning(f"Contact with id: {contact_id} not found")
        return None
    await db.delete(db_contact)
    await db.commit()
    logger.info(f"Contact deleted: {db_contact}")
    return db_contact


async def search_contacts(
    db: AsyncSession, first_name: str = None, last_name: str = None, email: str = None
):
    logger.info(
        f"Searching contacts with first_name: {first_name}, last_name: {last_name}, email: {email}"
    )
    query = select(Contact)
    if first_name:
        query = query.where(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Contact.email.ilike(f"%{email}%"))
    result = await db.execute(query)
    contacts = result.scalars().all()
    logger.info(f"Contacts found: {contacts}")
    return contacts


async def get_contacts_with_upcoming_birthdays(db: AsyncSession):
    logger.info("Fetching contacts with upcoming birthdays")
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)
    query = (
        select(Contact)
        .where(Contact.birthday >= today)
        .where(Contact.birthday <= upcoming)
    )
    result = await db.execute(query)
    contacts = result.scalars().all()
    logger.info(f"Contacts with upcoming birthdays: {contacts}")
    return contacts
