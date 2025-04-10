from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Contact(Base):
    """
    Represents a contact entity in the database.

    Attributes:
        id (int): The primary key of the contact.
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (str): The unique email address of the contact.
        phone (str): The phone number of the contact.
        birthday (date): The birthday of the contact.
        additional_data (str): Any additional information about the contact.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=False)
    birthday = Column(Date, nullable=False)
    additional_data = Column(Text, nullable=True)
