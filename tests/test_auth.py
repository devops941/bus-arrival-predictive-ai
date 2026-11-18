"""
Tests for Authentication, JWT, Lockout, and Repositories.
Verifies lockout policy (5 failed attempts locks for 15 minutes),
role/owner scoping, and JWT generation & verification.
Cleans up MONGODB_TEST_DB_NAME after tests.
"""

import os
from datetime import datetime, timezone, timedelta
import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException

# Configure valid test environment before importing config/app
os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["MONGODB_TIMEOUT_MS"] = "200"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"
os.environ["MONGODB_DB_NAME"] = "busarrival_test"
os.environ["MONGODB_TEST_DB_NAME"] = "busarrival_test"

from src.config import get_settings
from backend.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from src.db.repositories.user_repo import UserRepository
from src.db.repositories.base import BaseRepository
from backend.routers.auth import register, login, refresh_token_endpoint, get_current_user_profile
from backend.schemas import UserRegisterRequest, UserLoginRequest, TokenRefreshRequest


class InMemoryCollection:
    """Mock MongoDB collection for testing repositories without requiring external network."""
    def __init__(self):
        self.docs = []
        self._next_id = 1

    def find_one(self, query):
        for doc in self.docs:
            match = True
            for k, v in query.items():
                if k == "$or":
                    match = any(all(doc.get(subk) == subv for subk, subv in branch.items()) for branch in v)
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc.copy()
        return None

    def find(self, query=None):
        query = query or {}
        matches = []
        for doc in self.docs:
            match = True
            for k, v in query.items():
                if k == "$or":
                    match = any(all(doc.get(subk) == subv for subk, subv in branch.items()) for branch in v)
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                matches.append(doc.copy())

        class MockCursor:
            def __init__(self, data):
                self._data = data

            def skip(self, n):
                self._data = self._data[n:]
                return self

            def limit(self, n):
                self._data = self._data[:n]
                return self

            def sort(self, sort_keys):
                return self

            def __iter__(self):
                return iter(self._data)

        return MockCursor(matches)

    def insert_one(self, document):
        doc = document.copy()
        if "_id" not in doc:
            doc["_id"] = str(self._next_id)
            self._next_id += 1
        if "id" not in doc:
            doc["id"] = str(doc["_id"])
        self.docs.append(doc)
        res = MagicMock()
        res.inserted_id = doc["_id"]
        return res

    def update_one(self, query, update):
        target = self.find_one(query)
        if target:
            for doc in self.docs:
                if doc.get("id") == target.get("id") or doc.get("_id") == target.get("_id"):
                    if "$set" in update:
                        doc.update(update["$set"])
                    res = MagicMock()
                    res.modified_count = 1
                    res.matched_count = 1
                    return res
        res = MagicMock()
        res.modified_count = 0
        res.matched_count = 0
        return res

    def update_many(self, query, update):
        matches = list(self.find(query))
        count = 0
        for m in matches:
            for doc in self.docs:
                if doc.get("id") == m.get("id") or doc.get("_id") == m.get("_id"):
                    if "$set" in update:
                        doc.update(update["$set"])
                    count += 1
        res = MagicMock()
        res.modified_count = count
        res.matched_count = count
        return res

    def delete_one(self, query):
        target = self.find_one(query)
        if target:
            self.docs = [d for d in self.docs if d.get("id") != target.get("id")]
            res = MagicMock()
            res.deleted_count = 1
            return res
        res = MagicMock()
        res.deleted_count = 0
        return res

    def delete_many(self, query=None):
        query = query or {}
        matches = list(self.find(query))
        matched_ids = {m.get("id", m.get("_id")) for m in matches}
        self.docs = [d for d in self.docs if d.get("id", d.get("_id")) not in matched_ids]
        res = MagicMock()
        res.deleted_count = len(matches)
        return res

    def count_documents(self, query=None):
        return len(list(self.find(query)))

    def bulk_write(self, requests, ordered=False):
        upserted = 0
        modified = 0
        for req in requests:
            # UpdateOne support
            q = getattr(req, "_filter", {})
            update = getattr(req, "_doc", {})
            upsert = getattr(req, "_upsert", False)

            target = self.find_one(q)
            if target:
                for doc in self.docs:
                    if doc.get("id") == target.get("id"):
                        if "$set" in update:
                            doc.update(update["$set"])
                        modified += 1
                        break
            elif upsert:
                new_doc = dict(q)
                if "$set" in update:
                    new_doc.update(update["$set"])
                if "$setOnInsert" in update:
                    new_doc.update(update["$setOnInsert"])
                self.insert_one(new_doc)
                upserted += 1

        res = MagicMock()
        res.upserted_count = upserted
        res.modified_count = modified
        return res


class MockDatabase:
    def __init__(self, name="busarrival_test"):
        self.name = name
        self.collections = {}

    def __getitem__(self, item):
        if item not in self.collections:
            self.collections[item] = InMemoryCollection()
        return self.collections[item]

    def command(self, cmd):
        if cmd == "ping":
            return {"ok": 1.0}
        return {"ok": 1.0}

    def list_collection_names(self):
        return list(self.collections.keys())

    def create_collection(self, name, validator=None):
        return self[name]


class TestAuthenticationAndLockout(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        self.user_repo = UserRepository(self.mock_db)

    def tearDown(self):
        # Clean up test DB state
        self.mock_db.collections.clear()

    def test_password_hashing(self):
        """Verify bcrypt password hashing and verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_jwt_access_and_refresh_tokens(self):
        """Verify JWT generation, token types, and claims decoding."""
        data = {"sub": "user_123", "email": "test@busarrival.local", "role": "analyst"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        decoded_access = decode_token(access_token)
        self.assertEqual(decoded_access["sub"], "user_123")
        self.assertEqual(decoded_access["role"], "analyst")
        self.assertEqual(decoded_access["type"], "access")

        decoded_refresh = decode_token(refresh_token)
        self.assertEqual(decoded_refresh["sub"], "user_123")
        self.assertEqual(decoded_refresh["type"], "refresh")

    def test_lockout_after_five_failed_attempts(self):
        """
        Verify Acceptance Criteria:
        Account locks after 5 failed login attempts for 15 minutes.
        """
        user_id = self.user_repo.create_user(
            email="commuter@transit.org",
            hashed_password=hash_password("ValidPassword123!"),
            role="passenger",
        )

        user = self.user_repo.find_by_id(user_id)
        self.assertFalse(self.user_repo.is_locked(user))

        # Attempts 1 to 4 should increment attempts but NOT lock
        for attempt in range(1, 5):
            res = self.user_repo.record_failed_login(user_id, max_failed=5, lockout_minutes=15)
            self.assertEqual(res["attempts"], attempt)
            self.assertFalse(res["locked"])
            user = self.user_repo.find_by_id(user_id)
            self.assertFalse(self.user_repo.is_locked(user))

        # 5th attempt must trigger lock
        res = self.user_repo.record_failed_login(user_id, max_failed=5, lockout_minutes=15)
        self.assertEqual(res["attempts"], 5)
        self.assertTrue(res["locked"])
        self.assertIsNotNone(res["locked_until"])

        user = self.user_repo.find_by_id(user_id)
        self.assertTrue(self.user_repo.is_locked(user))

        # Reset failed logins clears lockout
        self.user_repo.reset_failed_logins(user_id)
        user = self.user_repo.find_by_id(user_id)
        self.assertFalse(self.user_repo.is_locked(user))
        self.assertEqual(user["failed_login_attempts"], 0)

    def test_role_and_owner_filtering(self):
        """Verify BaseRepository role-based query scoping."""
        base_repo = BaseRepository("routes", self.mock_db)

        # Admin gets unscoped query
        admin_query = base_repo.filter_by_role_and_owner(
            base_query={"active": True},
            user_role="admin",
            user_id="admin_1"
        )
        self.assertEqual(admin_query, {"active": True})

        # Non-admin with owner enforcement gets scoped to their created records
        analyst_query = base_repo.filter_by_role_and_owner(
            base_query={"active": True},
            user_role="analyst",
            user_id="analyst_42",
            enforce_owner=True
        )
        self.assertIn("$or", analyst_query)
        self.assertEqual(analyst_query["active"], True)


class TestAuthAPIRoutes(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        self.user_repo = UserRepository(self.mock_db)
        self.audit_repo = MagicMock()
        self.mock_request = MagicMock()
        self.mock_request.client.host = "127.0.0.1"

    def tearDown(self):
        self.mock_db.collections.clear()

    def test_register_login_and_me_flow(self):
        """Full auth journey: Register -> Login -> Me profile."""
        reg_req = UserRegisterRequest(
            email="driver@busarrival.local",
            password="Password123!",
            full_name="Transit Driver",
            role="analyst",
        )
        reg_res = register(
            req=reg_req,
            request=self.mock_request,
            user_repo=self.user_repo,
            audit_repo=self.audit_repo,
        )
        self.assertIsNotNone(reg_res.access_token)
        self.assertIsNotNone(reg_res.refresh_token)
        self.assertEqual(reg_res.email, "driver@busarrival.local")

        # Login with correct credentials
        login_res = login(
            req=UserLoginRequest(email="driver@busarrival.local", password="Password123!"),
            request=self.mock_request,
            user_repo=self.user_repo,
            audit_repo=self.audit_repo,
        )
        self.assertIsNotNone(login_res.access_token)
        token = login_res.access_token

        # Decode token and verify profile
        payload = decode_token(token)
        user_doc = self.user_repo.find_by_id(payload["sub"])
        me_profile = get_current_user_profile(user_doc)
        self.assertEqual(me_profile.email, "driver@busarrival.local")
        self.assertEqual(me_profile.role, "analyst")

    def test_login_lockout_endpoint(self):
        """Verify lockout triggers HTTP 403 on 5th failed attempt."""
        self.user_repo.create_user(
            email="operator@busarrival.local",
            hashed_password=hash_password("RealSecret123!"),
            role="analyst"
        )

        # 4 failed attempts raise 401
        for _ in range(4):
            with self.assertRaises(HTTPException) as ctx:
                login(
                    req=UserLoginRequest(email="operator@busarrival.local", password="WrongPassword!"),
                    request=self.mock_request,
                    user_repo=self.user_repo,
                    audit_repo=self.audit_repo,
                )
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("attempts remaining", ctx.exception.detail["detail"])

        # 5th attempt raises 403 ACCOUNT_LOCKED
        with self.assertRaises(HTTPException) as ctx5:
            login(
                req=UserLoginRequest(email="operator@busarrival.local", password="WrongPassword!"),
                request=self.mock_request,
                user_repo=self.user_repo,
                audit_repo=self.audit_repo,
            )
        self.assertEqual(ctx5.exception.status_code, 403)
        self.assertEqual(ctx5.exception.detail["code"], "ACCOUNT_LOCKED")


if __name__ == "__main__":
    unittest.main()
