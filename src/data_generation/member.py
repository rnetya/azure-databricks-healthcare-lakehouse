"""Generate deterministic synthetic healthcare Member CSV snapshots."""

import csv
import hashlib
import json
import random
from datetime import date, datetime, time, timezone
from pathlib import Path

COLUMNS = [
    "MemberId",
    "FirstName",
    "LastName",
    "DateOfBirth",
    "GenderCode",
    "AddressLine1",
    "City",
    "StateCode",
    "ZipCode",
    "MemberStatus",
    "SourceUpdatedAt",
]

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley"]
LAST_NAMES = ["Carter", "Brooks", "Parker", "Reed", "Morgan", "Hayes"]
LOCATIONS = [
    ("Dover", "DE", "19901"),
    ("Wilmington", "DE", "19801"),
    ("Baltimore", "MD", "21201"),
    ("Philadelphia", "PA", "19102"),
    ("Richmond", "VA", "23219"),
]


def generate_member(
    rng: random.Random,
    output_dir: Path,
    settings: dict,
) -> Path:
    """Generate a full Member snapshot and its delivery manifest."""
    count = settings["record_count"]
    snapshot_date = date.fromisoformat(settings["snapshot_date"])
    if snapshot_date > date.today():
        raise ValueError("Snapshot date cannot be in the future")

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"member_{snapshot_date:%Y%m%d}.csv"
    csv_path = output_dir / filename

    updated_at = (
        datetime.combine(snapshot_date, time(12, 0), tzinfo=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()

        for number in range(1, count + 1):
            city, state, zip_code = rng.choice(LOCATIONS)
            birth_year = rng.randint(1940, min(2020, snapshot_date.year))
            birth_date = date(
                birth_year,
                rng.randint(1, 12),
                rng.randint(1, 28),
            )

            writer.writerow(
                {
                    "MemberId": f"M{number:06d}",
                    "FirstName": rng.choice(FIRST_NAMES),
                    "LastName": rng.choice(LAST_NAMES),
                    "DateOfBirth": birth_date.isoformat(),
                    "GenderCode": rng.choice(["M", "F", "U"]),
                    "AddressLine1": f"{rng.randint(100, 9999)} Main St",
                    "City": city,
                    "StateCode": state,
                    "ZipCode": zip_code,
                    "MemberStatus": rng.choice(["ACTIVE", "INACTIVE"]),
                    "SourceUpdatedAt": updated_at,
                }
            )

    checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    manifest = {
        "dataset": "member",
        "snapshot_date": snapshot_date.isoformat(),
        "filename": filename,
        "expected_record_count": count,
        "checksum_algorithm": "SHA256",
        "checksum": checksum,
    }

    manifest_path = output_dir / f"member_{snapshot_date:%Y%m%d}.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return csv_path
