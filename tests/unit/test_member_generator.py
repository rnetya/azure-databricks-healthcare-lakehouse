"""Unit tests for the synthetic Member CSV generator."""

import csv
import hashlib
import json
import random
from datetime import date, datetime
from pathlib import Path

import pytest

from data_generation.member import COLUMNS, generate_member


def run_generator(tmp_path: Path, count: int = 10, seed: int = 42):
    return generate_member(
        random.Random(seed),
        tmp_path,
        {
            "record_count": count,
            "snapshot_date": "2026-10-17",
        },
    )


def read_members(path: Path):
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames, list(reader)


def test_member_record_count(tmp_path):
    path = run_generator(tmp_path, count=100)
    _, records = read_members(path)

    assert len(records) == 100


def test_member_schema(tmp_path):
    path = run_generator(tmp_path)
    columns, _ = read_members(path)

    assert columns == COLUMNS
    assert len(columns) == 11


def test_member_ids_are_unique(tmp_path):
    path = run_generator(tmp_path, count=100)
    _, records = read_members(path)

    ids = [record["MemberId"] for record in records]

    assert len(ids) == len(set(ids))
    assert ids[0] == "M000001"
    assert ids[-1] == "M000100"


def test_member_business_domains(tmp_path):
    path = run_generator(tmp_path, count=100)
    _, records = read_members(path)

    for record in records:
        assert record["FirstName"]
        assert record["LastName"]
        assert record["GenderCode"] in {"M", "F", "U"}
        assert record["MemberStatus"] in {"ACTIVE", "INACTIVE"}
        assert len(record["StateCode"]) == 2


def test_member_dates(tmp_path):
    path = run_generator(tmp_path, count=100)
    _, records = read_members(path)

    snapshot_date = date(2026, 10, 17)

    for record in records:
        birth_date = date.fromisoformat(record["DateOfBirth"])
        assert birth_date <= snapshot_date

        timestamp = record["SourceUpdatedAt"]
        assert timestamp.endswith("Z")
        assert datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def test_member_manifest_checksum(tmp_path):
    path = run_generator(tmp_path, count=100)

    manifest_path = tmp_path / "member_20261017.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    checksum = hashlib.sha256(path.read_bytes()).hexdigest()

    assert manifest["expected_record_count"] == 100
    assert manifest["snapshot_date"] == "2026-10-17"
    assert manifest["filename"] == path.name
    assert manifest["checksum"] == checksum


def test_member_deterministic_replay(tmp_path):
    path = run_generator(tmp_path, count=100)
    first_checksum = hashlib.sha256(path.read_bytes()).hexdigest()

    path = run_generator(tmp_path, count=100)
    second_checksum = hashlib.sha256(path.read_bytes()).hexdigest()

    assert first_checksum == second_checksum


def test_member_invalid_snapshot_date(tmp_path):
    with pytest.raises(ValueError):
        generate_member(
            random.Random(42),
            tmp_path,
            {
                "record_count": 10,
                "snapshot_date": "invalid-date",
            },
        )


def test_member_future_snapshot_date(tmp_path):
    with pytest.raises(ValueError):
        generate_member(
            random.Random(42),
            tmp_path,
            {
                "record_count": 10,
                "snapshot_date": "2099-01-01",
            },
        )
