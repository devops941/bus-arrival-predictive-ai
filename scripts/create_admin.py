"""
BusArrival AI - Bootstrap Administrator Script
Creates or updates the primary system administrator using settings from .env.
Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --email custom_admin@busarrival.local --password strongpassword123
"""

import sys
import argparse
from pathlib import Path

# Ensure repo root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings
from src.db.mongo import get_database, ensure_indexes, apply_collection_validators
from src.db.repositories.user_repo import UserRepository
from src.db.repositories.audit_repo import AuditRepository
from backend.security import hash_password


def create_or_update_admin(email: str = None, password: str = None, db_name: str = None):
    settings = get_settings()
    target_email = (email or settings.ADMIN_EMAIL).strip().lower()
    target_password = password or settings.ADMIN_PASSWORD

    db = get_database(db_name)
    apply_collection_validators(db)
    ensure_indexes(db)

    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)

    existing_user = user_repo.get_by_email(target_email)
    hashed_pw = hash_password(target_password)

    if existing_user:
        user_repo.update_by_id(existing_user["id"], {
            "hashed_password": hashed_pw,
            "role": "admin",
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        })
        user_id = existing_user["id"]
        action = "ADMIN_BOOTSTRAP_UPDATED"
        print(f"[+] Administrator account '{target_email}' successfully updated to role 'admin'.")
    else:
        user_id = user_repo.create_user(
            email=target_email,
            hashed_password=hashed_pw,
            role="admin",
            full_name="System Administrator",
            is_active=True,
        )
        action = "ADMIN_BOOTSTRAP_CREATED"
        print(f"[+] Administrator account '{target_email}' successfully created with role 'admin'.")

    audit_repo.log_event(
        action=action,
        entity_type="user",
        entity_id=user_id,
        user_id=user_id,
        user_email=target_email,
        details={"source": "scripts/create_admin.py"},
    )
    return user_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap BusArrival AI Administrator Account")
    parser.add_argument("--email", help="Administrator email (defaults to ADMIN_EMAIL in .env)")
    parser.add_argument("--password", help="Administrator password (defaults to ADMIN_PASSWORD in .env)")
    parser.add_argument("--db", help="Target database name (defaults to MONGODB_DB_NAME in .env)")
    args = parser.parse_args()

    try:
        create_or_update_admin(args.email, args.password, args.db)
    except Exception as exc:
        print(f"[!] Failed to create administrator: {exc}", file=sys.stderr)
        sys.exit(1)
