import os
import time
import json
from security.auth import authenticate

TOKEN_CACHE_FILE = ".ion_token_cache.json"


def get_token():
    """
    Return a valid ION API token.
    Uses cached token if still valid, otherwise fetches a new one.
    """

    # Try to read cached token
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE) as f:
                cached = json.load(f)

            if cached.get("expires_at", 0) > time.time():
                return cached["access_token"]

        except Exception:
            # corrupted cache --> ignore and fetch new token
            pass

    # Get new token
    result = authenticate()
    token = result["access_token"]

    # 2 hour token → store slightly less to be safe
    expires_at = time.time() + 7100

    with open(TOKEN_CACHE_FILE, "w") as f:
        json.dump({
            "access_token": token,
            "expires_at": expires_at
        }, f)

    return token
