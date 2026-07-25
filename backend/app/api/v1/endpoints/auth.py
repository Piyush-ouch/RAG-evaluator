"""
Authentication API Endpoints

Handles user registration, login, token refresh, logout,
and OAuth flows for Google and GitHub.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
import structlog
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.core.constants import AuthProvider, UserRole
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: DbSession,
) -> LoginResponse:
    """
    Register a new user and create their organization.

    Creates the user, organization, and billing account in a single transaction.
    Returns JWT tokens for immediate login.
    """
    # Check if email already exists
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictError("An account with this email already exists.")

    # Create organization
    from python_slugify import slugify
    org_slug = slugify(request.organization_name)

    # Ensure unique slug
    slug_check = select(Organization).where(Organization.slug == org_slug)
    result = await db.execute(slug_check)
    if result.scalar_one_or_none():
        org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(
        name=request.organization_name,
        slug=org_slug,
        plan="free",
        settings={},
    )
    db.add(org)
    await db.flush()

    # Create user
    user = User(
        org_id=org.id,
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole.OWNER.value,
        auth_provider=AuthProvider.LOCAL.value,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    # Create billing account
    from app.models.billing import BillingAccount
    billing = BillingAccount(
        org_id=org.id,
        plan="free",
        evaluation_limit=100,
    )
    db.add(billing)

    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"org_id": str(org.id), "role": user.role},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("user_registered", user_id=str(user.id), org_id=str(org.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user, from_attributes=True),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: DbSession,
) -> LoginResponse:
    """
    Authenticate with email and password.

    Returns JWT access and refresh tokens.
    """
    stmt = select(User).where(User.email == request.email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise AuthenticationError("Invalid email or password.")

    if not verify_password(request.password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated.")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"org_id": str(user.org_id), "role": user.role},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("user_logged_in", user_id=str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user, from_attributes=True),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: DbSession,
) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise AuthenticationError("Invalid refresh token.")

    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload.")

    stmt = select(User).where(User.id == uuid.UUID(user_id), User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User not found or deactivated.")

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"org_id": str(user.org_id), "role": user.role},
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(current_user: CurrentUser) -> dict:
    """Logout — invalidates the current session."""
    logger.info("user_logged_out", user_id=str(current_user.id))
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user, from_attributes=True)


# ---------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------

@router.get("/google")
async def google_oauth_redirect() -> RedirectResponse:
    """Redirect to Google OAuth consent screen."""
    settings = get_settings()
    if not settings.google_client_id:
        raise ValidationError("Google OAuth is not configured.")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(
        f"{k}={v}" for k, v in params.items()
    )
    return RedirectResponse(url=url)


@router.get("/google/callback")
async def google_oauth_callback(
    code: str,
    db: DbSession,
) -> LoginResponse:
    """Handle Google OAuth callback."""
    settings = get_settings()

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()

        # Get user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    return await _handle_oauth_user(
        db=db,
        provider=AuthProvider.GOOGLE,
        provider_id=userinfo["id"],
        email=userinfo["email"],
        first_name=userinfo.get("given_name", ""),
        last_name=userinfo.get("family_name", ""),
        avatar_url=userinfo.get("picture"),
    )


# ---------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------

@router.get("/github")
async def github_oauth_redirect() -> RedirectResponse:
    """Redirect to GitHub OAuth consent screen."""
    settings = get_settings()
    if not settings.github_client_id:
        raise ValidationError("GitHub OAuth is not configured.")

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "user:email read:user",
    }
    url = "https://github.com/login/oauth/authorize?" + "&".join(
        f"{k}={v}" for k, v in params.items()
    )
    return RedirectResponse(url=url)


@router.get("/github/callback")
async def github_oauth_callback(
    code: str,
    db: DbSession,
) -> LoginResponse:
    """Handle GitHub OAuth callback."""
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()

        # Get user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        github_user = user_resp.json()

        # Get primary email
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        emails = email_resp.json()
        primary_email = next(
            (e["email"] for e in emails if e.get("primary")),
            github_user.get("email"),
        )

    name_parts = (github_user.get("name") or "GitHub User").split(" ", 1)

    return await _handle_oauth_user(
        db=db,
        provider=AuthProvider.GITHUB,
        provider_id=str(github_user["id"]),
        email=primary_email,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        avatar_url=github_user.get("avatar_url"),
    )


# ---------------------------------------------------------
# Shared OAuth Handler
# ---------------------------------------------------------

async def _handle_oauth_user(
    db: AsyncSession,
    provider: AuthProvider,
    provider_id: str,
    email: str,
    first_name: str,
    last_name: str,
    avatar_url: str | None = None,
) -> LoginResponse:
    """
    Handle OAuth user — find existing or create new.

    If the user exists (matched by email), link the OAuth provider.
    If new, create user + organization.
    """
    from python_slugify import slugify

    stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Link OAuth provider if not already linked
        if not user.auth_provider_id:
            user.auth_provider = provider.value
            user.auth_provider_id = provider_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        user.last_login_at = datetime.now(timezone.utc)
    else:
        # Create organization
        org_slug = slugify(f"{first_name}-{last_name}-org")
        org = Organization(name=f"{first_name}'s Organization", slug=org_slug)
        db.add(org)
        await db.flush()

        user = User(
            org_id=org.id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            role=UserRole.OWNER.value,
            auth_provider=provider.value,
            auth_provider_id=provider_id,
            is_active=True,
            is_verified=True,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.flush()

        from app.models.billing import BillingAccount
        billing = BillingAccount(org_id=org.id, plan="free", evaluation_limit=100)
        db.add(billing)

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"org_id": str(user.org_id), "role": user.role},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("oauth_login", provider=provider.value, user_id=str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user, from_attributes=True),
    )
