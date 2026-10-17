"""Unit tests for the synthetic data generator CLI."""

import json

import pytest

from data_generation.cli import main


def test_list_datasets(capsys):
    result = main(["--list"])
    output = capsys.readouterr().out

    assert result == 0
    assert "member: enabled (csv)" in output
    assert "eligibility: enabled (parquet)" in output
    assert "claims: enabled (sqlserver)" in output
    assert "provider: enabled (json)" in output
    assert "service_events: enabled (avro)" in output
    assert "reference: enabled (csv)" in output


def test_member_generator_runs(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    config = {
        "project": "azure-databricks-healthcare-lakehouse",
        "environment": "dev",
        "random_seed": 42,
        "snapshot_date": "2026-10-17",
        "output_directory": "sample-data/generated",
        "datasets": {
            "member": {
                "enabled": True,
                "record_count": 10,
                "format": "csv",
            }
        },
    }

    config_path = tmp_path / "generator.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = main(
        [
            "--config",
            str(config_path),
            "--dataset",
            "member",
        ]
    )

    assert result == 0
    assert "Generated:" in capsys.readouterr().out
    assert (tmp_path / "sample-data/generated/member/member_20261017.csv").exists()


def test_unknown_dataset(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--dataset", "unknown"])

    assert error.value.code == 2
    assert "Unknown dataset" in capsys.readouterr().err


def test_missing_action():
    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 2
