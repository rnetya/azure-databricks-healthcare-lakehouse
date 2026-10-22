"""Incremental Eligibility delivery configuration and date resolution."""

import csv
import hashlib
import json
import random
import tempfile
from datetime import date, datetime, time, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from data_generation.eligibility import ELIGIBILITY_SCHEMA, PROGRAM_CODES

VALID_OPERATIONS = ("INSERT", "UPDATE", "DELETE")


def load_incremental_config(
    config_path: str | Path = "config/eligibility-incremental.json",
) -> dict:
    """Load and validate the incremental Eligibility configuration."""
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Incremental configuration not found: {path}")

    with path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Incremental configuration must be a JSON object.")

    if config.get("dataset") != "eligibility":
        raise ValueError("Dataset must be eligibility.")

    if config.get("delivery_type") != "INCREMENTAL":
        raise ValueError("Delivery type must be INCREMENTAL.")

    try:
        baseline_date = date.fromisoformat(config["baseline_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid or missing baseline_date.") from exc

    if baseline_date > date.today():
        raise ValueError("Baseline date cannot be in the future.")

    operations = config.get("operations")

    if not isinstance(operations, dict):
        raise ValueError("Operations must be a JSON object.")

    if set(operations) != set(VALID_OPERATIONS):
        raise ValueError("Operations must define INSERT, UPDATE, and DELETE.")

    for operation, count in operations.items():
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError(f"{operation} count must be a non-negative integer.")

    seed = config.get("random_seed")

    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("random_seed must be an integer.")

    resolve_delivery_date(config)

    return config


def resolve_delivery_date(
    config: dict,
    run_date: date | None = None,
) -> date:
    """Resolve the configured delivery date or the execution date."""
    configured_date = config.get("delivery_date")

    if configured_date is None:
        resolved_date = run_date if run_date is not None else date.today()
    else:
        try:
            resolved_date = date.fromisoformat(configured_date)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid delivery_date.") from exc

    if resolved_date > date.today():
        raise ValueError("Delivery date cannot be in the future.")

    try:
        baseline_date = date.fromisoformat(config["baseline_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid baseline_date.") from exc

    if resolved_date <= baseline_date:
        raise ValueError("Incremental delivery date must be after baseline date.")

    return resolved_date


def validate_delivery_manifest(
    manifest: dict,
    parquet_path: Path,
    rows: list[dict],
    baseline_date: date,
    schema: pa.Schema,
) -> None:
    """Validate delivery metadata against the actual Parquet contents."""

    # Validate the physical Parquet schema.
    if not schema.equals(ELIGIBILITY_SCHEMA):
        raise ValueError("Eligibility Parquet schema mismatch.")

    # Validate the date encoded in the delivery filename.
    date_text = parquet_path.stem.removeprefix("eligibility_")

    if not date_text.isdigit() or len(date_text) != 8:
        raise ValueError("Invalid Eligibility delivery filename.")

    filename_date = date.fromisoformat(f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}")

    delivery_type = manifest.get("delivery_type")

    if delivery_type == "BASELINE":
        if filename_date != baseline_date:
            raise ValueError("Baseline delivery date mismatch.")

        if manifest.get("snapshot_date") != baseline_date.isoformat():
            raise ValueError("Baseline manifest snapshot date mismatch.")

        if any(row["OperationType"] != "INSERT" for row in rows):
            raise ValueError("Baseline must contain only INSERT operations.")

    elif delivery_type == "INCREMENTAL":
        if manifest.get("delivery_date") != filename_date.isoformat():
            raise ValueError("Incremental manifest delivery date mismatch.")

        if manifest.get("baseline_date") != baseline_date.isoformat():
            raise ValueError("Incremental baseline reference mismatch.")

        if filename_date <= baseline_date:
            raise ValueError("Incremental date must follow baseline.")

    else:
        raise ValueError("Invalid manifest delivery type.")

    if manifest.get("dataset") != "eligibility":
        raise ValueError("Invalid manifest dataset.")

    if manifest.get("filename") != parquet_path.name:
        raise ValueError("Manifest filename mismatch.")

    if manifest.get("checksum_algorithm") != "SHA256":
        raise ValueError("Unsupported checksum algorithm.")

    if manifest.get("expected_record_count") != len(rows):
        raise ValueError("Manifest record count mismatch.")

    if not rows:
        return

    sequences = [row["SourceChangeSequence"] for row in rows]

    if manifest.get("delivery_type") == "INCREMENTAL":
        if manifest.get("starting_sequence") != min(sequences):
            raise ValueError("Manifest starting sequence mismatch.")

        if manifest.get("ending_sequence") != max(sequences):
            raise ValueError("Manifest ending sequence mismatch.")

        from collections import Counter

        operation_counts = dict(Counter(row["OperationType"] for row in rows))

        if manifest.get("operation_counts") != {
            operation: operation_counts.get(operation, 0)
            for operation in ("INSERT", "UPDATE", "DELETE")
        }:
            raise ValueError("Manifest operation counts mismatch.")

    elif manifest.get("delivery_type") != "BASELINE":
        raise ValueError("Invalid manifest delivery type.")


def reconstruct_eligibility_state(
    output_root: Path,
    baseline_date: date,
    delivery_date: date,
    include_highest_id: bool = False,
) -> tuple[dict[str, dict], int] | tuple[dict[str, dict], int, int]:
    """Rebuild Eligibility state from validated prior deliveries."""
    eligibility_dir = output_root / "eligibility"
    baseline_name = f"eligibility_{baseline_date:%Y%m%d}"

    baseline_path = eligibility_dir / f"{baseline_name}.parquet"
    baseline_manifest = eligibility_dir / f"{baseline_name}.manifest.json"

    if not baseline_path.is_file():
        raise FileNotFoundError(f"Eligibility baseline missing: {baseline_path}")

    if not baseline_manifest.is_file():
        raise FileNotFoundError(f"Eligibility baseline manifest missing: {baseline_manifest}")

    state: dict[str, dict] = {}
    last_sequence = 0
    highest_historical_id = 0

    delivery_files = [baseline_path]

    for path in eligibility_dir.glob("eligibility_*.parquet"):
        if path == baseline_path:
            continue

        date_text = path.stem.removeprefix("eligibility_")

        try:
            file_date = date.fromisoformat(f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}")
        except ValueError as exc:
            raise ValueError(f"Invalid Eligibility delivery filename: {path.name}") from exc

        if baseline_date < file_date < delivery_date:
            delivery_files.append(path)

    delivery_files.sort()

    for path in delivery_files:
        manifest_path = path.with_suffix(".manifest.json")

        if not manifest_path.is_file():
            raise FileNotFoundError(f"Delivery manifest missing: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        checksum = hashlib.sha256(path.read_bytes()).hexdigest()

        if manifest.get("checksum") != checksum:
            raise ValueError(f"Checksum mismatch for Eligibility delivery: {path.name}")

        table = pq.read_table(path)

        if manifest.get("expected_record_count") != table.num_rows:
            raise ValueError(f"Record count mismatch for Eligibility delivery: {path.name}")

        rows = table.to_pylist()

        validate_delivery_manifest(
            manifest,
            path,
            rows,
            baseline_date,
            table.schema,
        )

        rows.sort(key=lambda row: row["SourceChangeSequence"])

        for row in rows:
            sequence = row["SourceChangeSequence"]
            eligibility_id = row["EligibilityId"]
            operation = row["OperationType"]

            if sequence != last_sequence + 1:
                raise ValueError(
                    f"Invalid SourceChangeSequence: expected "
                    f"{last_sequence + 1}, received {sequence}"
                )

            if operation == "INSERT":
                if eligibility_id in state:
                    raise ValueError(f"Duplicate Eligibility INSERT: {eligibility_id}")

                if (
                    not isinstance(eligibility_id, str)
                    or len(eligibility_id) < 2
                    or not eligibility_id.startswith("E")
                    or not eligibility_id[1:].isdigit()
                    or int(eligibility_id[1:]) <= 0
                ):
                    raise ValueError(f"Invalid Eligibility ID: {eligibility_id}")

                numeric_id = int(eligibility_id[1:])

                if numeric_id <= highest_historical_id:
                    raise ValueError(f"Reused or out-of-order Eligibility ID: {eligibility_id}")

                state[eligibility_id] = row
                highest_historical_id = numeric_id

            elif operation == "UPDATE":
                if eligibility_id not in state:
                    raise ValueError(f"UPDATE references missing Eligibility: {eligibility_id}")
                state[eligibility_id] = row

            elif operation == "DELETE":
                if eligibility_id not in state:
                    raise ValueError(f"DELETE references missing Eligibility: {eligibility_id}")
                del state[eligibility_id]

            else:
                raise ValueError(f"Unsupported operation: {operation}")

            last_sequence = sequence

    if include_highest_id:
        return state, last_sequence, highest_historical_id

    return state, last_sequence


def load_member_ids(
    output_root: Path,
    baseline_date: date,
) -> list[str]:
    """Load valid Member IDs from the Member baseline CSV."""
    member_path = output_root / "member" / f"member_{baseline_date:%Y%m%d}.csv"

    if not member_path.is_file():
        raise FileNotFoundError(f"Member baseline missing: {member_path}")

    with member_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or "MemberId" not in reader.fieldnames:
            raise ValueError(f"MemberId column missing: {member_path}")

        member_ids = sorted(
            {
                row["MemberId"].strip()
                for row in reader
                if row.get("MemberId") and row["MemberId"].strip()
            }
        )

    if not member_ids:
        raise ValueError(f"No valid Member IDs found: {member_path}")

    return member_ids


def generate_incremental_eligibility(
    config: dict,
    output_root: Path,
) -> Path:
    """Generate a deterministic incremental Eligibility delivery."""
    delivery_date = resolve_delivery_date(config)
    baseline_date = date.fromisoformat(config["baseline_date"])

    eligibility_dir = output_root / "eligibility"
    filename = f"eligibility_{delivery_date:%Y%m%d}.parquet"
    parquet_path = eligibility_dir / filename
    manifest_path = eligibility_dir / (f"eligibility_{delivery_date:%Y%m%d}.manifest.json")

    if parquet_path.exists() != manifest_path.exists():
        raise RuntimeError(
            f"Incomplete Eligibility delivery detected for {delivery_date}. "
            "Parquet and manifest must both exist. "
            "Investigate the interrupted publication before retrying."
        )

    if parquet_path.exists() and manifest_path.exists():
        raise FileExistsError(f"Eligibility delivery already exists: {delivery_date}")

    state, last_sequence, highest_id = reconstruct_eligibility_state(
        output_root,
        baseline_date,
        delivery_date,
        include_highest_id=True,
    )

    operations = config["operations"]
    insert_count = operations["INSERT"]
    update_count = operations["UPDATE"]
    delete_count = operations["DELETE"]

    if update_count + delete_count > len(state):
        raise ValueError("Not enough existing Eligibility records for UPDATE and DELETE.")

    rng = random.Random(f"{config['random_seed']}:eligibility:{delivery_date.isoformat()}")

    updated_at = datetime.combine(delivery_date, time(12, 0), tzinfo=timezone.utc)

    update_candidates = sorted(
        eligibility_id
        for eligibility_id, row in state.items()
        if row["EligibilityStatus"] == "ACTIVE"
        and row["CoverageStartDate"] is not None
        and row["CoverageStartDate"] <= delivery_date
        and (row["CoverageEndDate"] is None or row["CoverageEndDate"] >= delivery_date)
    )

    if update_count > len(update_candidates):
        raise ValueError("Not enough eligible records available for UPDATE.")

    update_ids = rng.sample(update_candidates, update_count)

    delete_candidates = sorted(set(state) - set(update_ids))

    if delete_count > len(delete_candidates):
        raise ValueError("Not enough remaining records available for DELETE.")

    delete_ids = rng.sample(delete_candidates, delete_count)

    records = []
    next_sequence = last_sequence + 1

    # INSERT: New Eligibility records.
    # highest_id was already obtained from validated historical reconstruction.
    member_ids = load_member_ids(output_root, baseline_date) if insert_count > 0 else []

    for index in range(1, insert_count + 1):
        highest_id += 1
        member_id = rng.choice(member_ids)

        records.append(
            {
                "EligibilityId": f"E{highest_id:06d}",
                "MemberId": member_id,
                "ProgramCode": rng.choice(PROGRAM_CODES),
                "CoverageStartDate": delivery_date,
                "CoverageEndDate": None,
                "EligibilityStatus": "ACTIVE",
                "SourceUpdatedAt": updated_at,
                "OperationType": "INSERT",
                "SourceChangeSequence": next_sequence,
            }
        )
        next_sequence += 1

    # UPDATE: Change existing records without changing their IDs.
    for eligibility_id in update_ids:
        row = apply_eligibility_update(
            state[eligibility_id],
            delivery_date,
            updated_at,
            next_sequence,
        )

        records.append(row)
        next_sequence += 1

    # DELETE: Emit tombstones.
    for eligibility_id in delete_ids:
        records.append(
            {
                "EligibilityId": eligibility_id,
                "MemberId": None,
                "ProgramCode": None,
                "CoverageStartDate": None,
                "CoverageEndDate": None,
                "EligibilityStatus": None,
                "SourceUpdatedAt": updated_at,
                "OperationType": "DELETE",
                "SourceChangeSequence": next_sequence,
            }
        )
        next_sequence += 1

    table = pa.Table.from_pylist(records, schema=ELIGIBILITY_SCHEMA)

    eligibility_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".eligibility_staging_",
        dir=eligibility_dir,
    ) as staging_dir:
        staging_path = Path(staging_dir)
        staged_parquet = staging_path / filename

        pq.write_table(
            table,
            staged_parquet,
            compression="snappy",
        )

        # Verify the staged Parquet file before publication.
        verified_table = pq.read_table(staged_parquet)

        if not verified_table.schema.equals(ELIGIBILITY_SCHEMA):
            raise ValueError("Generated Eligibility schema mismatch.")

        if verified_table.num_rows != len(records):
            raise ValueError("Generated Eligibility record count mismatch.")

        checksum = hashlib.sha256(staged_parquet.read_bytes()).hexdigest()

        manifest = {
            "dataset": "eligibility",
            "delivery_type": "INCREMENTAL",
            "baseline_date": baseline_date.isoformat(),
            "delivery_date": delivery_date.isoformat(),
            "filename": filename,
            "expected_record_count": len(records),
            "operation_counts": operations,
            "starting_sequence": last_sequence + 1,
            "ending_sequence": next_sequence - 1,
            "checksum_algorithm": "SHA256",
            "checksum": checksum,
        }

        staged_manifest = staging_path / manifest_path.name

        staged_manifest.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        # Publish the Parquet file first, then the completion marker.
        if parquet_path.exists() or manifest_path.exists():
            raise FileExistsError(f"Eligibility delivery already exists: {delivery_date}")

        staged_parquet.replace(parquet_path)
        staged_manifest.replace(manifest_path)

    return parquet_path


def get_highest_historical_eligibility_id(
    output_root: Path,
    baseline_date: date,
    delivery_date: date,
) -> int:
    """Find the highest Eligibility ID assigned before a delivery."""
    eligibility_dir = output_root / "eligibility"
    highest_id = 0

    for path in sorted(eligibility_dir.glob("eligibility_*.parquet")):
        date_text = path.stem.removeprefix("eligibility_")

        try:
            file_date = date.fromisoformat(f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}")
        except ValueError as exc:
            raise ValueError(f"Invalid Eligibility filename: {path.name}") from exc

        if not baseline_date <= file_date < delivery_date:
            continue

        table = pq.read_table(path, columns=["EligibilityId", "OperationType"])

        for row in table.to_pylist():
            if row["OperationType"] != "INSERT":
                continue

            eligibility_id = row["EligibilityId"]

            if not eligibility_id.startswith("E"):
                raise ValueError(f"Invalid Eligibility ID: {eligibility_id}")

            numeric_id = int(eligibility_id[1:])
            highest_id = max(highest_id, numeric_id)

    return highest_id


def apply_eligibility_update(
    row: dict,
    delivery_date: date,
    updated_at: datetime,
    sequence: int,
) -> dict:
    """Apply a valid incremental termination to an Eligibility record."""
    updated_row = row.copy()

    coverage_start = updated_row["CoverageStartDate"]
    coverage_end = updated_row["CoverageEndDate"]

    if coverage_start is None:
        raise ValueError("CoverageStartDate cannot be null for UPDATE.")

    if coverage_start > delivery_date:
        raise ValueError("Cannot terminate coverage before its start date.")

    if coverage_end is not None and coverage_end < delivery_date:
        raise ValueError("Cannot extend previously ended coverage through termination.")

    updated_row["EligibilityStatus"] = "TERMINATED"
    updated_row["CoverageEndDate"] = delivery_date
    updated_row["SourceUpdatedAt"] = updated_at
    updated_row["OperationType"] = "UPDATE"
    updated_row["SourceChangeSequence"] = sequence

    return updated_row
