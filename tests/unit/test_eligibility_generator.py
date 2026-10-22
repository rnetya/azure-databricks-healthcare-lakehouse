"""Unit tests for synthetic Eligibility Parquet generation."""

import csv
import hashlib
import json
import random
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from data_generation.eligibility import (
    ELIGIBILITY_SCHEMA,
    PROGRAM_CODES,
    generate_eligibility,
    load_member_ids,
)

SNAPSHOT_DATE = "2026-10-17"


@pytest.fixture
def member_csv(tmp_path: Path) -> Path:
    """Create a small synthetic Member source for isolated tests."""
    path = tmp_path / "member_20261017.csv"

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["MemberId"])
        for number in range(1, 11):
            writer.writerow([f"M{number:06d}"])

    return path


def generate_test_file(
    tmp_path: Path,
    member_csv: Path,
    count: int = 20,
    seed: int = 42,
) -> Path:
    """Generate an isolated Eligibility delivery."""
    return generate_eligibility(
        random.Random(seed),
        tmp_path / "eligibility",
        {
            "record_count": count,
            "snapshot_date": SNAPSHOT_DATE,
            "member_csv_path": str(member_csv),
        },
    )


def test_eligibility_record_count(tmp_path, member_csv):
    path = generate_test_file(tmp_path, member_csv)
    table = pq.read_table(path)

    assert table.num_rows == 20
    assert table.num_columns == 9


def test_eligibility_schema(tmp_path, member_csv):
    path = generate_test_file(tmp_path, member_csv)
    table = pq.read_table(path)

    assert table.schema.equals(ELIGIBILITY_SCHEMA)
    assert table.schema.field("CoverageStartDate").type == pa.date32()
    assert table.schema.field("SourceUpdatedAt").type == pa.timestamp("us", tz="UTC")
    assert table.schema.field("SourceChangeSequence").type == pa.int64()


def test_eligibility_ids_and_sequences(tmp_path, member_csv):
    path = generate_test_file(tmp_path, member_csv)
    rows = pq.read_table(path).to_pylist()

    ids = [row["EligibilityId"] for row in rows]
    sequences = [row["SourceChangeSequence"] for row in rows]

    assert len(ids) == len(set(ids))
    assert ids[0] == "E000001"
    assert ids[-1] == "E000020"
    assert sequences == list(range(1, 21))


def test_eligibility_member_references(tmp_path, member_csv):
    path = generate_test_file(tmp_path, member_csv)
    rows = pq.read_table(path).to_pylist()

    valid_member_ids = set(load_member_ids(member_csv))

    assert all(row["MemberId"] in valid_member_ids for row in rows)
    assert len({row["MemberId"] for row in rows}) == 10


def test_eligibility_business_rules(tmp_path, member_csv):
    path = generate_test_file(tmp_path, member_csv)
    rows = pq.read_table(path).to_pylist()

    for row in rows:
        assert row["ProgramCode"] in PROGRAM_CODES
        assert row["EligibilityStatus"] in {
            "ACTIVE",
            "TERMINATED",
            "PENDING",
        }
        assert row["OperationType"] == "INSERT"

        assert row["CoverageStartDate"] <= date.fromisoformat(SNAPSHOT_DATE)

        if row["CoverageEndDate"] is not None:
            assert row["CoverageEndDate"] >= row["CoverageStartDate"]


def test_eligibility_manifest_checksum(tmp_path, member_csv):
    path = generate_test_file(tmp_path, member_csv)

    manifest_path = path.with_suffix(".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["dataset"] == "eligibility"
    assert manifest["delivery_type"] == "BASELINE"
    assert manifest["snapshot_date"] == SNAPSHOT_DATE
    assert manifest["expected_record_count"] == 20
    assert manifest["filename"] == path.name
    assert manifest["checksum_algorithm"] == "SHA256"
    assert manifest["checksum"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_eligibility_deterministic_replay(tmp_path, member_csv):
    first_path = generate_test_file(tmp_path, member_csv)
    first_checksum = hashlib.sha256(first_path.read_bytes()).hexdigest()

    second_path = generate_test_file(tmp_path, member_csv)
    second_checksum = hashlib.sha256(second_path.read_bytes()).hexdigest()

    assert first_checksum == second_checksum


def test_missing_member_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        generate_eligibility(
            random.Random(42),
            tmp_path / "eligibility",
            {
                "record_count": 10,
                "snapshot_date": SNAPSHOT_DATE,
                "member_csv_path": str(tmp_path / "missing.csv"),
            },
        )


def test_duplicate_member_ids_rejected(tmp_path):
    path = tmp_path / "members.csv"
    path.write_text(
        "MemberId\nM000001\nM000001\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate Member IDs"):
        load_member_ids(path)
