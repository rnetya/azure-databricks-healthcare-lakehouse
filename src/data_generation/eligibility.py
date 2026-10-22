"""Generate synthetic healthcare Eligibility Parquet deliveries."""

import csv
import hashlib
import json
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ELIGIBILITY_SCHEMA = pa.schema(
    [
        pa.field("EligibilityId", pa.string(), nullable=False),
        pa.field("MemberId", pa.string()),
        pa.field("ProgramCode", pa.string()),
        pa.field("CoverageStartDate", pa.date32()),
        pa.field("CoverageEndDate", pa.date32()),
        pa.field("EligibilityStatus", pa.string()),
        pa.field("SourceUpdatedAt", pa.timestamp("us", tz="UTC")),
        pa.field("OperationType", pa.string(), nullable=False),
        pa.field("SourceChangeSequence", pa.int64(), nullable=False),
    ]
)


def load_member_ids(member_csv_path: Path) -> list[str]:
    """Read valid Member IDs from the generated Member CSV."""
    if not member_csv_path.is_file():
        raise FileNotFoundError(f"Member baseline not found: {member_csv_path}")

    with member_csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None or "MemberId" not in reader.fieldnames:
            raise ValueError("Member CSV is missing the MemberId column.")

        member_ids = [row["MemberId"] for row in reader]

    if not member_ids:
        raise ValueError("Member baseline contains no records.")

    if any(not member_id for member_id in member_ids):
        raise ValueError("Member baseline contains an empty MemberId.")

    if len(member_ids) != len(set(member_ids)):
        raise ValueError("Member baseline contains duplicate Member IDs.")

    return member_ids


PROGRAM_CODES = ["MEDICAID", "CHIP", "THIP", "ABD", "LTSS", "HCBS"]


def generate_eligibility(
    rng: random.Random,
    output_dir: Path,
    settings: dict,
) -> Path:
    """Generate a deterministic Eligibility baseline Parquet delivery."""
    record_count = settings["record_count"]
    snapshot_date = date.fromisoformat(settings["snapshot_date"])

    if not isinstance(record_count, int) or isinstance(record_count, bool):
        raise ValueError("Eligibility record_count must be an integer.")

    if record_count <= 0:
        raise ValueError("Eligibility record_count must be positive.")

    if snapshot_date > date.today():
        raise ValueError("Snapshot date cannot be in the future.")

    member_path = Path(settings["member_csv_path"])
    member_ids = load_member_ids(member_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"eligibility_{snapshot_date:%Y%m%d}.parquet"
    parquet_path = output_dir / filename

    updated_at = datetime.combine(
        snapshot_date,
        time(12, 0),
        tzinfo=timezone.utc,
    )

    records = []

    for number in range(1, record_count + 1):
        member_id = member_ids[(number - 1) % len(member_ids)]

        days_before_snapshot = rng.randint(0, 365 * 3)
        coverage_start = snapshot_date - timedelta(days=days_before_snapshot)

        status = rng.choices(
            ["ACTIVE", "TERMINATED", "PENDING"],
            weights=[75, 20, 5],
            k=1,
        )[0]

        if status == "ACTIVE":
            coverage_end = None
        elif status == "TERMINATED":
            coverage_end = coverage_start + timedelta(
                days=rng.randint(
                    0,
                    (snapshot_date - coverage_start).days,
                )
            )
        else:
            coverage_end = None

        records.append(
            {
                "EligibilityId": f"E{number:06d}",
                "MemberId": member_id,
                "ProgramCode": rng.choice(PROGRAM_CODES),
                "CoverageStartDate": coverage_start,
                "CoverageEndDate": coverage_end,
                "EligibilityStatus": status,
                "SourceUpdatedAt": updated_at,
                "OperationType": "INSERT",
                "SourceChangeSequence": number,
            }
        )

    table = pa.Table.from_pylist(
        records,
        schema=ELIGIBILITY_SCHEMA,
    )

    pq.write_table(
        table,
        parquet_path,
        compression="snappy",
    )

    checksum = hashlib.sha256(parquet_path.read_bytes()).hexdigest()

    manifest = {
        "dataset": "eligibility",
        "snapshot_date": snapshot_date.isoformat(),
        "delivery_type": "BASELINE",
        "filename": filename,
        "expected_record_count": record_count,
        "checksum_algorithm": "SHA256",
        "checksum": checksum,
    }

    manifest_path = output_dir / (f"eligibility_{snapshot_date:%Y%m%d}.manifest.json")

    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return parquet_path
