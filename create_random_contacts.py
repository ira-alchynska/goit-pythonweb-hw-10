import requests
from faker import Faker

fake = Faker()
url = "http://127.0.0.1:8000/api/contacts/"

for _ in range(30):
    data = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number(),
        "birthday": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
        "additional_data": fake.text(max_nb_chars=50)
    }
    response = requests.post(url, json=data)
    if response.status_code in (200, 201):
        print("Contact created:", response.json())
    else:
        print("Error creating contact:", response.status_code, response.text)
