from pymongo import MongoClient
from credentials import mongodb_uri

client = MongoClient(mongodb_uri)

db = client.hack_to_hire
collection = db.users

def add_user_to_database(fln, email, phone_number):
    user = {
        "fln": fln,
        "email": email,
        "phone_number": phone_number,
        "last_status": "none",
        "last_arrival_gate": "none",
        "last_arrival_terminal": "none",
        "last_departure_gate": "none",
        "last_departure_terminal": "none",
        "last_delay": "none"
    }
    return collection.insert_one(user)

def get_users_from_database():
    return list(collection.find({}))

def update_user_info_to_database(fln, new_status, new_arrival_gate, new_arrival_terminal, new_departure_gate, new_departure_terminal, new_delay):
    collection.update_one(
        {"fln": fln},
        {"$set": {
            "last_status": new_status,
            "last_arrival_gate": new_arrival_gate,
            "last_arrival_terminal": new_arrival_terminal,
            "last_departure_gate": new_departure_gate,
            "last_departure_terminal": new_departure_terminal,
            "last_delay": new_delay
        }}
    )

def check_contact_in_db(flight_number, contact):
    return collection.find_one({"fln": flight_number, "$or": [{"email": contact}, {"phone_number": contact}]}) is not None
