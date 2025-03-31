from datetime import date
from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_data: str = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: EmailStr = None
    phone: str = None
    birthday: date = None
    additional_data: str = None


class Contact(ContactBase):
    id: int

    class Config:
        from_attributes = True
