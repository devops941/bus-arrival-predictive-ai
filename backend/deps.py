"""
BusArrival AI - FastAPI Dependency Injection
Provides database sessions, current user extraction from JWT, role guards, and rate limiting.
"""

from typing import Optional, List, Dict, Any, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import get_settings
from src.db.mongo import get_database
from src.db.repositories.user_repo import UserRepository
from src.db.repositories.audit_repo import AuditRepository
from backend.security import decode_token


# Global Rate Limiter instance (SlowAPI)
limiter = Limiter(key_func=get_remote_address)

security_bearer = HTTPBearer(auto_error=False)


def get_db():
    """Dependency for injecting MongoDB database handle."""
    return get_database()


def get_user_repository(db=Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_audit_repository(db=Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Dict[str, Any]:
    """
    Authenticate Bearer JWT token and return active user document.
    Blocks if expired, invalid, inactive, or locked out.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Authentication credentials were not provided", "code": "AUTH_REQUIRED"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Authentication token has expired", "code": "TOKEN_EXPIRED"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Could not validate authentication credentials", "code": "INVALID_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token is not a valid access token", "code": "INVALID_TOKEN_TYPE"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token subject is missing", "code": "MALFORMED_TOKEN"},
        )

    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "User associated with this token no longer exists", "code": "USER_NOT_FOUND"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "User account has been deactivated", "code": "ACCOUNT_DEACTIVATED"},
        )

    if user_repo.is_locked(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "User account is locked due to excessive failed attempts", "code": "ACCOUNT_LOCKED"},
        )

    return user


def require_role(allowed_roles: List[str]) -> Callable:
    """Dependency factory checking that the authenticated user possesses an authorized role."""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "passenger")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "detail": f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )
        return current_user
    return role_checker
