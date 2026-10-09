"""Tests for healthcare validation helpers."""

from healthcare.validation import is_valid_member_id


def test_valid_member_id() -> None:
    assert is_valid_member_id("MEM12345")


def test_null_member_id() -> None:
    assert not is_valid_member_id(None)


def test_empty_member_id() -> None:
    assert not is_valid_member_id("")


def test_whitespace_member_id() -> None:
    assert not is_valid_member_id("   ")
