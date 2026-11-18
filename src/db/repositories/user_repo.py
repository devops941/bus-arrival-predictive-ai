"""
User Repository for MongoDB.
Manages user accounts, authentication records, lockout status, and role metadata.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("users", db)

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by normalized email address."""
        return self.find_one({"email": email.strip().lower()})

    def create_user(
        self,
        email: str,
        hashed_password: str,
        role: str = "passenger",
        full_name: Optional[str] = None,
        is_active: bool = True,
    ) -> str:
        """Create a new user account with default security counters."""
        now = datetime.now(timezone.utc)
        doc = {
            "email": email.strip().lower(),
            "hashed_password": hashed_password,
            "role": role,
            "full_name": full_name or "",
            "is_active": is_active,
            "failed_login_attempts": 0,
            "locked_until": None,
            "created_at": now,
            "updated_at": now,
        }
        return self.insert_one(doc)

    def is_locked(self, user: Dict[str, Any]) -> bool:
        """Check if user account is currently locked out."""
        locked_until = user.get("locked_until")
        if not locked_until:
            return False
        
        now = datetime.now(timezone.utc)
        if isinstance(locked_until, datetime):
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            return locked_until > now
        return False

    def record_failed_login(
        self,
        user_id: str,
        max_failed: int = 5,
        lockout_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Increment failed login counter. If counter reaches max_failed, lock account.
        Returns dict with current attempts and whether account is now locked.
        """
        user = self.find_by_id(user_id)
        if not user:
            return {"attempts": 0, "locked": False, "locked_until": None}

        current_attempts = user.get("failed_login_attempts", 0) + 1
        now = datetime.now(timezone.utc)
        updates: Dict[str, Any] = {
            "failed_login_attempts": current_attempts,
            "updated_at": now,
        }

        locked = False
        locked_until = None
        if current_attempts >= max_failed:
            locked = True
            locked_until = now + timedelta(minutes=lockout_minutes)
            updates["locked_until"] = locked_until

        self.update_by_id(user_id, updates)
        return {
            "attempts": current_attempts,
            "locked": locked,
            "locked_until": locked_until
        }

    def reset_failed_logins(self, user_id: str) -> None:
        """Reset failed login attempts counter and clear lockout upon successful authentication."""
        self.update_by_id(user_id, {
            "failed_login_attempts": 0,
            "locked_until": None,
            "updated_at": datetime.now(timezone.utc),
        })

    def update_password(self, user_id: str, hashed_password: str) -> bool:
        """Update user password hash and reset lockout counters."""
        return self.update_by_id(user_id, {
            "hashed_password": hashed_password,
            "failed_login_attempts": 0,
            "locked_until": None,
            "updated_at": datetime.now(timezone.utc),
        })

    def list_users(self, skip: int = 0, limit: int = 100, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """List user accounts with optional role filtering."""
        query = {"role": role} if role else {}
        return self.find_many(query, skip=skip, limit=limit, sort=[("created_at", -1)])
