"""Unit tests for incremental Eligibility processing."""

import hashlib
import json
from datetime import date, datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from data_generation.eligibility import ELIGIBILITY_SCHEMA
from data_generation.eligibility_incremental import (
    apply_eligibility_update,
    generate_incremental_eligibility,
    reconstruct_eligibility_state,
    resolve_delivery_date,
)


@pytest.fixture
def incremental_config():
    return {
        "dataset": "eligibility",
        "delivery_type": "INCREMENTAL",
        "baseline_date": "2026-10-17",
        "delivery_date": None,
        "random_seed": 42,
        "operations": {
            "INSERT": 100,
            "UPDATE": 150,
            "DELETE": 50,
        },
    }


def test_dynamic_delivery_date(incremental_config):
    result = resolve_delivery_date(
        incremental_config,
        run_date=date(2026, 10, 22),
    )

    assert result == date(2026, 10, 22)


def test_historical_delivery_date_override(incremental_config):
    incremental_config["delivery_date"] = "2026-10-18"

    result = resolve_delivery_date(incremental_config)

    assert result == date(2026, 10, 18)


@pytest.mark.parametrize(
    "delivery_date",
    ["2026-10-17", "2026-10-16"],
)
def test_delivery_date_must_follow_baseline(
    incremental_config,
    delivery_date,
):
    incremental_config["delivery_date"] = delivery_date

    with pytest.raises(ValueError, match="after baseline"):
        resolve_delivery_date(incremental_config)


def test_valid_eligibility_termination():
    original = {
        "EligibilityId": "E000001",
        "CoverageStartDate": date(2026, 1, 1),
        "CoverageEndDate": None,
        "EligibilityStatus": "ACTIVE",
    }

    updated_at = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)

    result = apply_eligibility_update(
        original,
        date(2026, 10, 22),
        updated_at,
        12001,
    )

    assert result["EligibilityId"] == "E000001"
    assert result["EligibilityStatus"] == "TERMINATED"
    assert result["CoverageEndDate"] == date(2026, 10, 22)
    assert result["SourceChangeSequence"] == 12001
    assert result["OperationType"] == "UPDATE"

    # Original record must remain unchanged.
    assert original["EligibilityStatus"] == "ACTIVE"
    assert original["CoverageEndDate"] is None


def test_cannot_terminate_before_coverage_start():
    original = {
        "EligibilityId": "E000001",
        "CoverageStartDate": date(2026, 10, 25),
        "CoverageEndDate": None,
        "EligibilityStatus": "ACTIVE",
    }

    with pytest.raises(ValueError, match="before its start"):
        apply_eligibility_update(
            original,
            date(2026, 10, 22),
            datetime(2026, 10, 22, tzinfo=timezone.utc),
            12001,
        )


def test_cannot_extend_terminated_coverage():
    original = {
        "EligibilityId": "E000001",
        "CoverageStartDate": date(2026, 1, 1),
        "CoverageEndDate": date(2026, 9, 30),
        "EligibilityStatus": "TERMINATED",
    }

    with pytest.raises(ValueError, match="Cannot extend"):
        apply_eligibility_update(
            original,
            date(2026, 10, 22),
            datetime(2026, 10, 22, tzinfo=timezone.utc),
            12001,
        )


def create_test_baseline(output_root):
    """Create a small, valid Eligibility baseline in an isolated directory."""
    # Create Member baseline for Eligibility INSERT references.
    member_dir = output_root / "member"
    member_dir.mkdir(parents=True, exist_ok=True)

    member_path = member_dir / "member_20261017.csv"

    member_path.write_text(
        "MemberId\n" + "".join(f"M{number:06d}\n" for number in range(1, 11)),
        encoding="utf-8",
    )

    directory = output_root / "eligibility"
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / "eligibility_20261017.parquet"

    records = [
        {
            "EligibilityId": f"E{number:06d}",
            "MemberId": f"M{number:06d}",
            "ProgramCode": "MEDICAID",
            "CoverageStartDate": date(2026, 1, 1),
            "CoverageEndDate": None,
            "EligibilityStatus": "ACTIVE",
            "SourceUpdatedAt": datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc),
            "OperationType": "INSERT",
            "SourceChangeSequence": number,
        }
        for number in range(1, 11)
    ]

    table = pa.Table.from_pylist(records, schema=ELIGIBILITY_SCHEMA)
    pq.write_table(table, path, compression="snappy")

    manifest = {
        "dataset": "eligibility",
        "snapshot_date": "2026-10-17",
        "delivery_type": "BASELINE",
        "filename": path.name,
        "expected_record_count": len(records),
        "checksum_algorithm": "SHA256",
        "checksum": hashlib.sha256(path.read_bytes()).hexdigest(),
    }

    manifest_path = path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return path, manifest_path


def test_reconstruction_rejects_corrupted_manifest(tmp_path):
    _, manifest_path = create_test_baseline(tmp_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["checksum"] = "invalid-checksum"
    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Checksum mismatch"):
        reconstruct_eligibility_state(
            tmp_path,
            date(2026, 10, 17),
            date(2026, 10, 18),
        )


def test_generator_rejects_existing_delivery(tmp_path, incremental_config):
    create_test_baseline(tmp_path)

    incremental_config["delivery_date"] = "2026-10-18"
    incremental_config["operations"] = {
        "INSERT": 2,
        "UPDATE": 3,
        "DELETE": 1,
    }

    first_path = generate_incremental_eligibility(
        incremental_config,
        tmp_path,
    )

    original_checksum = hashlib.sha256(first_path.read_bytes()).hexdigest()

    with pytest.raises(FileExistsError, match="already exists"):
        generate_incremental_eligibility(
            incremental_config,
            tmp_path,
        )

    assert hashlib.sha256(first_path.read_bytes()).hexdigest() == (original_checksum)


def test_multiple_incremental_deliveries(tmp_path, incremental_config):
    """Verify CDC continuity across two consecutive deliveries."""
    create_test_baseline(tmp_path)

    incremental_config["operations"] = {
        "INSERT": 2,
        "UPDATE": 3,
        "DELETE": 1,
    }

    # First incremental delivery.
    incremental_config["delivery_date"] = "2026-10-18"

    first_path = generate_incremental_eligibility(
        incremental_config,
        tmp_path,
    )

    first_rows = pq.read_table(first_path).to_pylist()

    assert len(first_rows) == 6
    assert [row["SourceChangeSequence"] for row in first_rows] == list(range(11, 17))

    state, sequence = reconstruct_eligibility_state(
        tmp_path,
        date(2026, 10, 17),
        date(2026, 10, 19),
    )

    assert len(state) == 11
    assert sequence == 16

    # Second incremental delivery.
    incremental_config["delivery_date"] = "2026-10-19"

    second_path = generate_incremental_eligibility(
        incremental_config,
        tmp_path,
    )

    second_rows = pq.read_table(second_path).to_pylist()

    assert len(second_rows) == 6
    assert [row["SourceChangeSequence"] for row in second_rows] == list(range(17, 23))

    final_state, final_sequence = reconstruct_eligibility_state(
        tmp_path,
        date(2026, 10, 17),
        date(2026, 10, 20),
    )

    assert len(final_state) == 12
    assert final_sequence == 22

    # Ensure INSERT identifiers were never reused.
    first_insert_ids = {
        row["EligibilityId"] for row in first_rows if row["OperationType"] == "INSERT"
    }

    second_insert_ids = {
        row["EligibilityId"] for row in second_rows if row["OperationType"] == "INSERT"
    }

    assert first_insert_ids.isdisjoint(second_insert_ids)

    # Verify historical ID continuity.
    assert first_insert_ids == {"E000011", "E000012"}
    assert second_insert_ids == {"E000013", "E000014"}


def test_deleted_highest_id_is_not_reused(tmp_path, incremental_config):
    """A deleted Eligibility ID must remain permanently reserved."""
    create_test_baseline(tmp_path)

    incremental_config["operations"] = {
        "INSERT": 0,
        "UPDATE": 0,
        "DELETE": 10,
    }
    incremental_config["delivery_date"] = "2026-10-18"

    # Delete every baseline record, including E000010.
    generate_incremental_eligibility(incremental_config, tmp_path)

    state, sequence, highest_id = reconstruct_eligibility_state(
        tmp_path,
        date(2026, 10, 17),
        date(2026, 10, 19),
        include_highest_id=True,
    )

    assert len(state) == 0
    assert sequence == 20
    assert highest_id == 10

    # Generate a new INSERT after every previous record was deleted.
    incremental_config["operations"] = {
        "INSERT": 1,
        "UPDATE": 0,
        "DELETE": 0,
    }
    incremental_config["delivery_date"] = "2026-10-19"

    new_path = generate_incremental_eligibility(
        incremental_config,
        tmp_path,
    )

    new_rows = pq.read_table(new_path).to_pylist()

    assert len(new_rows) == 1
    assert new_rows[0]["OperationType"] == "INSERT"
    assert new_rows[0]["EligibilityId"] == "E000011"
    assert new_rows[0]["SourceChangeSequence"] == 21
    assert new_rows[0]["MemberId"] is not None

    # Reconstruct the final state including the new delivery.
    final_state, final_sequence, final_highest_id = reconstruct_eligibility_state(
        tmp_path,
        date(2026, 10, 17),
        date(2026, 10, 20),
        include_highest_id=True,
    )

    assert len(final_state) == 1
    assert final_sequence == 21
    assert final_highest_id == 11
    assert "E000011" in final_state


def test_generator_rejects_incomplete_publication(
    tmp_path,
    incremental_config,
):
    """An orphaned Parquet file must block regeneration."""
    create_test_baseline(tmp_path)

    incremental_config["delivery_date"] = "2026-10-18"
    incremental_config["operations"] = {
        "INSERT": 1,
        "UPDATE": 0,
        "DELETE": 0,
    }

    orphan_path = tmp_path / "eligibility" / "eligibility_20261018.parquet"

    # Simulate interruption after Parquet publication,
    # but before manifest publication.
    orphan_path.write_bytes(b"incomplete-delivery")

    with pytest.raises(
        RuntimeError,
        match="Incomplete Eligibility delivery",
    ):
        generate_incremental_eligibility(
            incremental_config,
            tmp_path,
        )

    # The incomplete file must not be overwritten.
    assert orphan_path.read_bytes() == b"incomplete-delivery"
    assert not orphan_path.with_suffix(".manifest.json").exists()
