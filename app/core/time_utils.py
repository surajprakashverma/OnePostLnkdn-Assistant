"""
Datetime helper to safely compare timezone-aware and timezone-naive
datetimes, regardless of whether the underlying DB is SQLite (returns
naive) or PostgreSQL (returns aware).
"""
from datetime import datetime, timezone


def to_naive_utc(dt: datetime) -> datetime:
    """Strip tzinfo (if present) so comparisons are always apples-to-apples."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)