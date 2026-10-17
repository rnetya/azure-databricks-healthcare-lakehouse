"""Unit tests for the synthetic data generator CLI."""

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


def test_member_generator_not_implemented(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--dataset", "member"])

    assert error.value.code == 2
    assert "not yet implemented" in capsys.readouterr().err


def test_unknown_dataset(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--dataset", "unknown"])

    assert error.value.code == 2
    assert "Unknown dataset" in capsys.readouterr().err


def test_missing_action():
    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 2
