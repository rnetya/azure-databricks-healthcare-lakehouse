"""Unit tests for synthetic generator configuration."""

import json

import pytest

from data_generation.config import get_output_directory, load_config


def test_load_valid_config(tmp_path):
    config_path = tmp_path / "generator.json"
    config_path.write_text(
        json.dumps(
            {
                "project": "healthcare",
                "environment": "dev",
                "random_seed": 42,
                "output_directory": "generated",
                "datasets": {
                    "member": {
                        "enabled": True,
                        "format": "csv",
                        "record_count": 100,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["random_seed"] == 42
    assert config["datasets"]["member"]["record_count"] == 100


def test_missing_config_raises_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.json")


def test_invalid_seed_raises_error(tmp_path):
    config_path = tmp_path / "invalid.json"
    config_path.write_text(
        json.dumps(
            {
                "project": "healthcare",
                "environment": "dev",
                "random_seed": "invalid",
                "output_directory": "generated",
                "datasets": {"member": {"enabled": True, "format": "csv"}},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="random_seed"):
        load_config(config_path)


def test_output_directory_creation(tmp_path):
    config = {"output_directory": "generated/member"}

    output = get_output_directory(config, tmp_path)

    assert output.is_dir()
    assert output == tmp_path / "generated" / "member"


def test_output_directory_cannot_escape_project(tmp_path):
    config = {"output_directory": "../outside"}

    with pytest.raises(ValueError, match="inside the project root"):
        get_output_directory(config, tmp_path)
