import truststore
truststore.inject_into_ssl()

"""
Token Service
-------------
Creates and validates signed, time-limited JWT tokens used in the
Approve/Reject email links. The token only encodes the post_log_id
and an expiry â€” the actual "single-use" enforcement happens in the
approval route by checking the PostedLog.status in the DB (once
actioned, status != 'pending_approval', so a reused link is rejected).
"""
from datetime import datetime, timedelta, timezone

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.core.config import settings


def create_approval_token(post_log_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.APPROVAL_TOKEN_EXPIRE_HOURS)
    payload = {
        "post_log_id": post_log_id,
        "exp": expire,
        "type": "approval",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_approval_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return {"valid": True, "post_log_id": payload.get("post_log_id")}
    except ExpiredSignatureError:
        return {"valid": False, "error": "This approval link has expired."}
    except JWTError:
        return {"valid": False, "error": "This approval link is invalid."}
