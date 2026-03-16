"""Time helpers used across the project."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Return current UTC as a naive datetime for DB compatibility.

    This intentionally returns a naive UTC datetime because existing
    SQLAlchemy DateTime columns are configured without timezone=True.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
