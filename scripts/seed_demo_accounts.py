"""
Seed / Upsert Demo Accounts for BusArrival AI:
- admin@busarrival.local (role: admin)
- analyst@busarrival.local (role: analyst)
- passenger@busarrival.local (role: passenger)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.mongo import get_database
from src.db.repositories.user_repo import UserRepository
from backend.security import hash_password

DEMO_ACCOUNTS = [
    {
        "email": "admin@busarrival.local",
        "password": "AdminSecure2026!",
        "role": "admin",
        "full_name": "System Administrator",
    },
    {
        "email": "analyst@busarrival.local",
        "password": "AnalystPass123!",
        "role": "analyst",
        "full_name": "Transit Data Analyst",
    },
    {
        "email": "passenger@busarrival.local",
        "password": "PassengerPass123!",
        "role": "passenger",
        "full_name": "Madurai Commuter",
    },
]

def seed_demo_accounts():
    db = get_database()
    user_repo = UserRepository(db)
    print(f"Connecting to database '{db.name}' to seed demo accounts...")

    for acc in DEMO_ACCOUNTS:
        email = acc["email"].lower().strip()
        hashed = hash_password(acc["password"])
        existing = user_repo.get_by_email(email)

        if existing:
            user_repo.update_by_id(existing["id"], {
                "hashed_password": hashed,
                "role": acc["role"],
                "full_name": acc["full_name"],
                "is_active": True,
                "failed_login_attempts": 0,
                "locked_until": None,
            })
            print(f"✓ Updated demo account: {email} (role: {acc['role']})")
        else:
            user_id = user_repo.create_user(
                email=email,
                hashed_password=hashed,
                role=acc["role"],
                full_name=acc["full_name"],
                is_active=True,
            )
            print(f"✓ Created new demo account: {email} (role: {acc['role']}) -> ID: {user_id}")

    print("\nAll demo accounts are ready for sign-in!")

if __name__ == "__main__":
    seed_demo_accounts()
