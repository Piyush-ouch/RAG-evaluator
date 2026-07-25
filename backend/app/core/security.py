"""
Security Module — JWT, Password Hashing, Token Management

Handles all cryptographic operations:
- JWT access/refresh token generation and validation
- Password hashing with bcrypt
- API key generation and hashing
- Fernet encryption for stored secrets (e.g., LLM API keys)
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

logger = structlog.get_logger(__name__)

# Password hashing context — bcrypt with auto-upgrade
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------
# JWT Tokens
# ---------------------------------------------------------

def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The token subject (typically user ID as string).
        extra_claims: Additional claims to encode (e.g., org_id, role).
        expires_delta: Custom expiration. Defaults to settings.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    claims = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }

    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have a longer lifespan and contain minimal claims.
    They are used solely to obtain new access tokens.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

    claims = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "refresh",
        "jti": secrets.token_urlsafe(32),  # Unique ID for revocation
    }

    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Returns the full claims dictionary.
    Raises JWTError on invalid or expired tokens.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        raise


# ---------------------------------------------------------
# API Key Management
# ---------------------------------------------------------

def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key pair.

    Returns:
        tuple: (raw_key, key_hash)
            - raw_key: The plaintext key shown to the user ONCE.
            - key_hash: The bcrypt hash stored in the database.
    """
    # Prefix helps identify key type in logs (never reveals the secret)
    prefix = "rge_"
    raw_key = prefix + secrets.token_urlsafe(48)
    key_hash = pwd_context.hash(raw_key)
    return raw_key, key_hash


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    """Verify a raw API key against its stored hash."""
    return pwd_context.verify(raw_key, key_hash)


# ---------------------------------------------------------
# Fernet Encryption (for stored API keys, secrets)
# ---------------------------------------------------------

def get_fernet() -> Fernet:
    """Get the Fernet encryption instance from the configured key."""
    settings = get_settings()
    return Fernet(settings.encryption_key.encode())


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string. Returns the original plaintext."""
    f = get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
