"""
app/models/user.py
------------------
MongoDB document helpers for the users collection.

Updated: added mobile field and updated serialise_user accordingly.
"""

from datetime import datetime, timezone

USERS_COLLECTION = "users"


def build_user_document(
    name:            str,
    email:           str,
    hashed_password: str,
    mobile:          str = "",
) -> dict:
    """Return a new user document ready for insertion into MongoDB."""
    return {
        "name":       name.strip(),
        "email":      email.lower().strip(),
        "mobile":     mobile.strip(),
        "password":   hashed_password,
        "created_at": datetime.now(timezone.utc),
    }


def serialise_user(document: dict) -> dict:
    """Convert a raw MongoDB document to a JSON-serialisable dict."""
    return {
        "id":         str(document["_id"]),
        "name":       document["name"],
        "email":      document["email"],
        "mobile":     document.get("mobile", ""),
        "created_at": document["created_at"].isoformat()
                      if isinstance(document.get("created_at"), datetime)
                      else str(document.get("created_at", "")),
    }
