"""
Real password hashing and JWT issuance/verification - passlib and
python-jose were already in requirements.txt (the README claimed
"JWT-based authentication with refresh tokens" as a feature) but no auth
code existed anywhere in the codebase.

Deliberately basic: access tokens only, no refresh token rotation, no
role-based access control. This is enough to make leads genuinely
per-user rather than a shared, unauthenticated in-memory dict - it is not
the "enterprise-grade security" the old README claimed.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"

# Using bcrypt directly rather than through passlib's CryptContext:
# passlib 1.7.4 (last release, effectively unmaintained) runs an internal
# self-test against the installed bcrypt backend on first use, and that
# self-test itself breaks against bcrypt 5.x ("password cannot be longer
# than 72 bytes"). bcrypt itself works fine standalone.


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Returns the subject (user id) if the token is valid, else None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
