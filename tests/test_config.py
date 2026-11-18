"""
Tests for configuration loading and fail-fast validation.
Verifies that the application refuses to start with missing or placeholder credentials.
Works with both pytest and python -m unittest.
"""

import os
import unittest
from pydantic import ValidationError
from src.config import Settings


class TestConfigFailFast(unittest.TestCase):
    def setUp(self):
        # Save original environment
        self._orig_env = os.environ.copy()

    def tearDown(self):
        # Restore environment
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_missing_env_raises_validation_error(self):
        """Verify that Settings refuses to instantiate when required env variables are absent."""
        os.environ.pop("MONGODB_URI", None)
        os.environ.pop("JWT_SECRET", None)

        with self.assertRaises(ValidationError) as ctx:
            Settings(_env_file=None)

        errors = ctx.exception.errors()
        fields_with_errors = [err["loc"][0] for err in errors]
        self.assertIn("MONGODB_URI", fields_with_errors)
        self.assertIn("JWT_SECRET", fields_with_errors)

    def test_placeholder_mongodb_uri_raises_error(self):
        """Verify that Settings detects placeholder markers in MONGODB_URI."""
        os.environ["MONGODB_URI"] = "mongodb+srv://<db_user>:<url_encoded_password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
        os.environ["JWT_SECRET"] = "super-secret-key-that-is-at-least-32-chars-long"

        with self.assertRaises(ValidationError) as ctx:
            Settings(_env_file=None)

        errors = ctx.exception.errors()
        msg = str(errors[0]["msg"])
        self.assertIn("placeholder", msg.lower())

    def test_placeholder_jwt_secret_raises_error(self):
        """Verify that Settings detects placeholder markers in JWT_SECRET."""
        os.environ["MONGODB_URI"] = "mongodb+srv://realuser:realpass123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
        os.environ["JWT_SECRET"] = "change-me-to-a-long-random-string"

        with self.assertRaises(ValidationError) as ctx:
            Settings(_env_file=None)

        errors = ctx.exception.errors()
        msg = str(errors[0]["msg"])
        self.assertIn("placeholder", msg.lower())

    def test_short_jwt_secret_raises_error(self):
        """Verify that JWT_SECRET shorter than 32 characters is rejected."""
        os.environ["MONGODB_URI"] = "mongodb+srv://realuser:realpass123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
        os.environ["JWT_SECRET"] = "too-short-secret"

        with self.assertRaises(ValidationError) as ctx:
            Settings(_env_file=None)

        errors = ctx.exception.errors()
        msg = str(errors[0]["msg"])
        self.assertIn("at least 32 characters", msg)

    def test_invalid_mongodb_protocol_raises_error(self):
        """Verify that MONGODB_URI without mongodb:// or mongodb+srv:// is rejected."""
        os.environ["MONGODB_URI"] = "postgres://user:pass@localhost:5432/db"
        os.environ["JWT_SECRET"] = "super-secret-key-that-is-at-least-32-chars-long"

        with self.assertRaises(ValidationError) as ctx:
            Settings(_env_file=None)

        errors = ctx.exception.errors()
        msg = str(errors[0]["msg"])
        self.assertTrue("mongodb://" in msg or "mongodb+srv://" in msg)

    def test_valid_configuration_loads(self):
        """Verify that Settings properly instantiates when valid configuration is provided."""
        os.environ.pop("MONGODB_DB_NAME", None)
        os.environ["MONGODB_URI"] = "mongodb+srv://testuser:testpass123@cluster0.mongodb.net/?retryWrites=true&w=majority"
        os.environ["JWT_SECRET"] = "super-secure-production-ready-jwt-secret-key-32-bytes"

        settings = Settings(_env_file=None)
        self.assertTrue(settings.MONGODB_DB_NAME.startswith("busarrival"))
        self.assertEqual(settings.JWT_ACCESS_MINUTES, 30)
        self.assertIn("http://localhost:5173", settings.cors_origins_list)

    def test_uri_credentials_never_logged_or_exposed(self):
        """Verify Section 15 requirement: URI password is never exposed in logs or masked URI."""
        os.environ["MONGODB_URI"] = "mongodb+srv://secretuser:supersecretpass123@cluster0.mongodb.net/?retryWrites=true&w=majority"
        os.environ["JWT_SECRET"] = "super-secure-production-ready-jwt-secret-key-32-bytes"

        settings = Settings(_env_file=None)
        masked = settings.get_masked_uri()
        self.assertNotIn("supersecretpass123", masked)
        self.assertIn(":****@", masked)


if __name__ == "__main__":
    unittest.main()
