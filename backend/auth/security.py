"""
Security and Cryptography Utilities for PharmacyGuard.
Provides OWASP-compliant password hashing (PBKDF2-HMAC-SHA256)
and signed JWT session token generation and verification.
"""

import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

import jwt

# Dynamic JWT key handling: load from environment, or generate a cryptographically secure
# ephemeral 256-bit secret if not configured (never use hardcoded static secret strings).
_env_jwt_secret = os.getenv("JWT_SECRET_KEY")
if _env_jwt_secret and _env_jwt_secret.strip():
    JWT_SECRET_KEY = _env_jwt_secret.strip()
else:
    # Ephemeral CSPRNG secret prevents static credential compromise while ensuring local runnability
    JWT_SECRET_KEY = secrets.token_hex(32)
    import logging
    logging.getLogger("pharmacyguard.auth").warning(
        "SECURITY NOTICE: JWT_SECRET_KEY is not set. An ephemeral 256-bit secret has been generated "
        "for this process session. Set JWT_SECRET_KEY in .env for persistent multi-process sessions."
    )
JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12-hour hospital shift session
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a 16-byte random salt
    and 600,000 iterations.
    
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored PBKDF2-HMAC-SHA256 hash string
    using constant-time comparison to prevent timing attacks.
    """
    if not plain_password or not password_hash:
        return False
    
    try:
        parts = password_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])
        
        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations
        )
        return hmac.compare_digest(computed_key, expected_hash)
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Encodes and signs a JSON Web Token (JWT) containing user claims and expiration timestamp.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT token.
    Raises jwt.PyJWTError on expiration or invalid signature.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
