import os
import requests
from dotenv import load_dotenv

load_dotenv()

def authenticate():
    auth_url = os.environ.get("ION_AUTH_URL")
    client_id = os.environ.get("ION_CLIENT_ID")
    client_secret = os.environ.get("ION_CLIENT_SECRET")
    username = os.environ.get("ION_USERNAME")
    password = os.environ.get("ION_PASSWORD")

    required = [auth_url, client_id, client_secret, username, password]
    if not all(required):
        raise RuntimeError("Missing one or more required environment variables")

    payload = {
        "grant_type": "password",
        "username": username,
        "password": password
    }

    r = requests.post(
        auth_url,
        auth=(client_id, client_secret),
        data=payload
    )

    r.raise_for_status()
    return {
             "access_token": r.json()["access_token"],
             "expires_in": r.json()["expires_in"]
    }


# print(authenticate())
