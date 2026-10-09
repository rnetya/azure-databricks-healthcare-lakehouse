"""Reusable healthcare data validation helpers."""


def is_valid_member_id(value: str | None) -> bool:
    """Check whether a member identifier is present and nonblank."""
    return isinstance(value, str) and bool(value.strip())
