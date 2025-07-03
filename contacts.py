import json
import os

CONTACTS_FILE = "contacts.json"

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "w") as f:
            json.dump({}, f)
    with open(CONTACTS_FILE, "r") as f:
        return json.load(f)

def save_contacts(contacts):
    with open(CONTACTS_FILE, "w") as f:
        json.dump(contacts, f, indent=4)

def add_contact(user, contact):
    contacts = load_contacts()
    if user not in contacts:
        contacts[user] = []
    if contact in contacts[user]:
        return f"{contact} already in your contacts."
    contacts[user].append(contact)
    save_contacts(contacts)
    return f"{contact} added to your contacts."

def remove_contact(user, contact):
    contacts = load_contacts()
    if user not in contacts or contact not in contacts[user]:
        return f"{contact} not in your contacts."
    contacts[user].remove(contact)
    save_contacts(contacts)
    return f"{contact} removed from your contacts."

def get_contacts(user):
    contacts = load_contacts()
    return contacts.get(user, [])
