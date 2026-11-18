"""
Authentication Router.
Handles registration, login with lockout and rate limiting, token refresh, and logout.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
import jwt
from src.config import get_settings
from backend.deps import (
    get_user_repository,
    get_audit_repository,
    get_current_user,
    require_role,
    limiter,
)
from src.db.repositories.user_repo import UserRepository
from src.db.repositories.audit_repo import AuditRepository
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserResponse,
    PasswordChangeRequest,
    AdminResetPasswordRequest,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: UserRegisterRequest,
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Register a new user account."""
    existing = user_repo.get_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "A user with this email address already exists", "code": "EMAIL_ALREADY_EXISTS"},
        )

    # Note: Admin accounts can only be created by an existing admin or create_admin.py script
    requested_role = req.role if req.role in ("passenger", "analyst") else "passenger"

    hashed_pw = hash_password(req.password)
    user_id = user_repo.create_user(
        email=req.email,
        hashed_password=hashed_pw,
        role=requested_role,
        full_name=req.full_name,
    )

    settings = get_settings()
    token_data = {"sub": user_id, "email": req.email, "role": requested_role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_repo.log_event(
        action="USER_REGISTER",
        entity_type="user",
        entity_id=user_id,
        user_id=user_id,
        user_email=req.email,
        details={"role": requested_role},
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.JWT_ACCESS_MINUTES,
        user_id=user_id,
        email=req.email,
        role=requested_role,
        full_name=req.full_name,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    req: UserLoginRequest,
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """
    Authenticate user credentials.
    Enforces lockout policy: 5 failed attempts locks account for 15 minutes.
    """
    settings = get_settings()
    user = user_repo.get_by_email(req.email)
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not user:
        # Avoid user enumeration by returning standard message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Invalid email or password", "code": "INVALID_CREDENTIALS"},
        )

    # Check if account is currently locked out
    if user_repo.is_locked(user):
        locked_until = user.get("locked_until")
        minutes_remaining = settings.LOCKOUT_MINUTES
        if isinstance(locked_until, datetime):
            now = datetime.now(timezone.utc)
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            diff = (locked_until - now).total_seconds() / 60
            minutes_remaining = max(1, int(diff))

        audit_repo.log_event(
            action="LOGIN_ATTEMPT_WHILE_LOCKED",
            entity_type="user",
            entity_id=user.get("id"),
            user_id=user.get("id"),
            user_email=req.email,
            ip_address=client_ip,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "detail": f"Account is locked due to too many failed login attempts. Try again in {minutes_remaining} minutes.",
                "code": "ACCOUNT_LOCKED",
            },
        )

    # Verify password
    if not verify_password(req.password, user.get("hashed_password", "")):
        lock_res = user_repo.record_failed_login(
            user["id"],
            max_failed=settings.MAX_FAILED_LOGINS,
            lockout_minutes=settings.LOCKOUT_MINUTES,
        )

        audit_repo.log_event(
            action="LOGIN_FAILED",
            entity_type="user",
            entity_id=user.get("id"),
            user_id=user.get("id"),
            user_email=req.email,
            details={"attempts": lock_res["attempts"], "locked": lock_res["locked"]},
            ip_address=client_ip,
        )

        if lock_res["locked"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "detail": f"Too many failed attempts. Account has been locked for {settings.LOCKOUT_MINUTES} minutes.",
                    "code": "ACCOUNT_LOCKED",
                },
            )

        remaining_attempts = max(0, settings.MAX_FAILED_LOGINS - lock_res["attempts"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": f"Invalid email or password. {remaining_attempts} attempts remaining before account lockout.",
                "code": "INVALID_CREDENTIALS",
            },
        )

    # Success: reset failed logins counter
    user_repo.reset_failed_logins(user["id"])

    token_data = {"sub": user["id"], "email": user["email"], "role": user.get("role", "passenger")}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    audit_repo.log_event(
        action="LOGIN_SUCCESS",
        entity_type="user",
        entity_id=user["id"],
        user_id=user["id"],
        user_email=user["email"],
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.JWT_ACCESS_MINUTES,
        user_id=user["id"],
        email=user["email"],
        role=user.get("role", "passenger"),
        full_name=user.get("full_name"),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token_endpoint(
    req: TokenRefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Generate a new access token from a valid refresh token."""
    settings = get_settings()
    try:
        payload = decode_token(req.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Refresh token has expired", "code": "TOKEN_EXPIRED"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Invalid refresh token", "code": "INVALID_TOKEN"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Token is not a refresh token", "code": "INVALID_TOKEN_TYPE"},
        )

    user_id = payload.get("sub")
    user = user_repo.find_by_id(user_id)
    if not user or not user.get("is_active", True) or user_repo.is_locked(user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "User account is inactive or locked", "code": "ACCOUNT_DISABLED"},
        )

    new_access_token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "role": user.get("role", "passenger"),
    })

    return TokenRefreshResponse(
        access_token=new_access_token,
        expires_in_minutes=settings.JWT_ACCESS_MINUTES,
    )


@router.post("/logout")
def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Log user logout event."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_repo.log_event(
        action="LOGOUT",
        entity_type="user",
        entity_id=current_user.get("id"),
        user_id=current_user.get("id"),
        user_email=current_user.get("email"),
        ip_address=client_ip,
    )
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    """Retrieve currently authenticated user profile."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user.get("role", "passenger"),
        full_name=current_user.get("full_name"),
        is_active=current_user.get("is_active", True),
        failed_login_attempts=current_user.get("failed_login_attempts", 0),
        locked_until=current_user.get("locked_until"),
        created_at=current_user.get("created_at", datetime.now(timezone.utc)),
        updated_at=current_user.get("updated_at"),
    )


@router.post("/change-password")
def change_password(
    req: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Allow an authenticated user to update their password."""
    if not verify_password(req.old_password, current_user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Current password does not match", "code": "INCORRECT_PASSWORD"},
        )

    new_hash = hash_password(req.new_password)
    user_repo.update_password(current_user["id"], new_hash)

    audit_repo.log_event(
        action="PASSWORD_CHANGED",
        entity_type="user",
        entity_id=current_user["id"],
        user_id=current_user["id"],
        user_email=current_user["email"],
    )

    return {"detail": "Password updated successfully"}


@router.post("/reset")
def admin_reset_password(
    req: AdminResetPasswordRequest,
    current_admin: dict = Depends(require_role(["admin"])),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Administrator-issued password reset without requiring email delivery."""
    target_user = user_repo.find_by_id(req.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "USER_NOT_FOUND"},
        )

    new_hash = hash_password(req.new_password)
    user_repo.update_password(req.user_id, new_hash)

    audit_repo.log_event(
        action="ADMIN_PASSWORD_RESET",
        entity_type="user",
        entity_id=req.user_id,
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        details={"target_email": target_user.get("email")},
    )

    return {"detail": f"Password reset successfully for user {target_user.get('email')}"}
