"""
BusArrival AI - Application Configuration & Environment Settings
Fails fast when required environment variables or valid credentials are missing.
"""

from functools import lru_cache
import os
import sys
from typing import List
from pydantic import Field, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


# Known placeholder fragments that indicate the developer hasn't configured a real secret
PLACEHOLDER_MARKERS = [
    "<db_user>",
    "<url_encoded_password>",
    "<cluster-host>",
    "<cluster>",
    "<username>",
    "<password>",
    "change-me",
    "placeholder",
    "your-secret",
    "your_secret",
]


class Settings(BaseSettings):
    """
    Central configuration schema for BusArrival AI.
    Loads from .env file and environment variables.
    """
    # Application runtime
    APP_ENV: str = Field(default="development", description="Runtime environment (development, test, production)")
    APP_HOST: str = Field(default="127.0.0.1", description="Backend host interface")
    APP_PORT: int = Field(default=8000, description="Backend port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    CORS_ORIGINS: str = Field(default="http://localhost:5173", description="Comma-separated CORS allowed origins")

    # MongoDB Atlas settings
    MONGODB_URI: str = Field(..., validation_alias=AliasChoices("MONGODB_URI", "MONGO_URI"), description="MongoDB Atlas connection URI (never commit real credentials)")
    MONGODB_DB_NAME: str = Field(default="busarrival_ai", validation_alias=AliasChoices("MONGODB_DB_NAME", "DB_NAME"), description="Primary MongoDB database name")
    MONGODB_TEST_DB_NAME: str = Field(default="busarrival_test", description="Test database name")
    MONGODB_TIMEOUT_MS: int = Field(default=8000, description="MongoDB server selection timeout in milliseconds")

    # Authentication & Security
    JWT_SECRET: str = Field(..., description="Secret key used for signing JWT access and refresh tokens")
    JWT_ACCESS_MINUTES: int = Field(default=30, description="JWT access token expiry in minutes")
    JWT_REFRESH_DAYS: int = Field(default=7, description="JWT refresh token expiry in days")
    MAX_FAILED_LOGINS: int = Field(default=5, description="Maximum failed login attempts before lockout")
    LOCKOUT_MINUTES: int = Field(default=15, description="Lockout duration in minutes")
    ADMIN_EMAIL: str = Field(default="admin@busarrival.local", description="Bootstrap administrator email")
    ADMIN_PASSWORD: str = Field(default="change-me-strong", description="Bootstrap administrator initial password")

    # File paths & limits
    MODEL_DIR: str = Field(default="outputs/models", description="Trained model artifact directory")
    REPORT_DIR: str = Field(default="outputs/reports", description="Generated report directory")
    UPLOAD_DIR: str = Field(default="data/uploads", description="Data upload staging directory")
    MAX_UPLOAD_MB: int = Field(default=10, description="Maximum allowed file upload size in MB")
    RANDOM_SEED: int = Field(default=42, description="Global random seed for reproducibility")
    DRIFT_RATIO_THRESHOLD: float = Field(default=1.3, description="Drift alert ratio threshold")
    SCHEDULER_ENABLED: bool = Field(default=False, description="Enable background retrain/drift scheduler")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("MONGODB_URI")
    @classmethod
    def validate_mongodb_uri(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("MONGODB_URI must be a non-empty string.")

        val = v.strip()
        if not (val.startswith("mongodb://") or val.startswith("mongodb+srv://")):
            raise ValueError(
                "MONGODB_URI must begin with 'mongodb://' or 'mongodb+srv://'. "
                "Ensure your .env file contains a valid connection URI."
            )

        for marker in PLACEHOLDER_MARKERS:
            if marker in val.lower():
                raise ValueError(
                    f"MONGODB_URI contains placeholder token '{marker}'. "
                    "You must provide a real MongoDB Atlas URI in your local .env file. "
                    "Remember to never commit real credentials to Git."
                )

        return val

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("JWT_SECRET must be a non-empty string.")

        val = v.strip()
        for marker in PLACEHOLDER_MARKERS:
            if marker in val.lower():
                raise ValueError(
                    f"JWT_SECRET contains placeholder token '{marker}'. "
                    "Set a secure, unique secret key (at least 32 characters) in your local .env file."
                )

        if len(val) < 32:
            raise ValueError(
                f"JWT_SECRET is too short ({len(val)} chars). "
                "It must be at least 32 characters long to ensure cryptographic security."
            )

        return val

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list of cleaned origin URLs."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def get_masked_uri(self) -> str:
        """Returns a sanitized MongoDB URI string with password masked for safe logging."""
        import re
        return re.sub(r":([^@]+)@", ":****@", self.MONGODB_URI)


def print_env_error_banner(error_details: str) -> None:
    """Print an eye-catching, informative error message when configuration fails."""
    separator = "=" * 78
    message = f"""
{separator}
[!] BUSARRIVAL AI CONFIGURATION ERROR - STARTUP BLOCKED
{separator}
The application refused to start because essential environment settings are
missing or contain default placeholder values.

Details:
{error_details}

How to fix:
1. Ensure a local `.env` file exists at the root of the project:
   copy .env.example .env

2. Edit `.env` and configure real credentials:
   - MONGODB_URI: Replace '<db_user>', '<url_encoded_password>', etc.
     with your MongoDB Atlas connection string.
   - JWT_SECRET: Replace 'change-me-to-a-long-random-string' with a strong
     random string of at least 32 characters.

3. Note: NEVER commit real credentials to Git. `.env` is listed in `.gitignore`.
{separator}
"""
    sys.stderr.write(message)
    sys.stderr.flush()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and cache application settings.
    Terminates startup fast with a clean error message if configuration is invalid.
    """
    try:
        return Settings()
    except Exception as exc:
        print_env_error_banner(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    # When run directly, validate the current environment
    print("[*] Validating environment configuration...")
    settings = get_settings()
    print("[+] Configuration successfully validated!")
    print(f"    - Environment: {settings.APP_ENV}")
    print(f"    - Host: {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"    - Database Name: {settings.MONGODB_DB_NAME}")
    print(f"    - Test DB Name: {settings.MONGODB_TEST_DB_NAME}")
    print(f"    - Scheduler: {'Enabled' if settings.SCHEDULER_ENABLED else 'Disabled'}")
