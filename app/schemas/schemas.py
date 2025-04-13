from datetime import date
from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    """
    Base schema for contact-related data.

    Attributes:
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (EmailStr): The email address of the contact.
        phone (str): The phone number of the contact.
        birthday (date): The birthday of the contact.
        additional_data (str): Additional information about the contact.
    """
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_data: str = None


class ContactCreate(ContactBase):
    """
    Schema for creating a new contact.
    """
    pass


class ContactUpdate(BaseModel):
    """
    Schema for updating an existing contact.

    Attributes:
        first_name (Optional[str]): The updated first name of the contact.
        last_name (Optional[str]): The updated last name of the contact.
        email (Optional[EmailStr]): The updated email address of the contact.
        phone (Optional[str]): The updated phone number of the contact.
        birthday (Optional[date]): The updated birthday of the contact.
        additional_data (Optional[str]): The updated additional information about the contact.
    """
    first_name: str = None
    last_name: str = None
    email: EmailStr = None
    phone: str = None
    birthday: date = None
    additional_data: str = None


class Contact(ContactBase):
    """
    Schema for outputting contact data.

    Attributes:
        id (int): The unique identifier of the contact.
    """
    id: int

    class Config:
        from_attributes = True
