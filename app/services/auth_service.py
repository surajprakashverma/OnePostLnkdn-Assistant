import truststore
truststore.inject_into_ssl()

import hashlib
from datetime import datetime, timedelta, timezone

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from fastapi import Request, HTTPException

from app.core.config import settings


def hash_password(password: str) -> str:
    return hashlib.sha256((password + settings.JWT_SECRET_KEY).encode("utf-8")).hexdigest()


def verify_credentials(username: str, password: str) -> bool:
    if username != settings.ADMIN_USERNAME:
        return False
    return hash_password(password) == settings.ADMIN_PASSWORD_HASH


def create_session_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire, "type": "session"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_session_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("sub") != settings.ADMIN_USERNAME:
            return {"valid": False, "error": "Unknown user"}
        return {"valid": True, "username": payload.get("sub")}
    except ExpiredSignatureError:
        return {"valid": False, "error": "Session expired"}
    except JWTError:
        return {"valid": False, "error": "Invalid session"}


def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    result = decode_session_token(token)
    if not result["valid"]:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    return result["username"]