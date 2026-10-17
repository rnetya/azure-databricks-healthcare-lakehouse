"""Unit tests for the synthetic data generator engine."""

import csv

import pytest

from data_generation.generator import GeneratorEngine


@pytest.fixture
def config():
    return {
        "random_seed": 42,
        "output_directory": "generated",
        "datasets": {
            "member": {
                "enabled": True,
                "format": "csv",
                "record_count": 3,
            },
            "claims": {
                "enabled": False,
                "format": "sqlserver",
            },
        },
    }


def sample_member_generator(rng, output_dir, settings):
    """Create a small deterministic test dataset."""
    output_file = output_dir / "member.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["MemberId", "RandomValue"])

        for index in range(1, settings["record_count"] + 1):
            writer.writerow([f"M{index:06d}", rng.randint(1, 1000)])

    return output_file


def test_generator_creates_file(config, tmp_path):
    engine = GeneratorEngine(config, tmp_path)
    engine.register("member", sample_member_generator)

    result = engine.run("member")

    assert result.is_file()
    assert result.parent.name == "member"


def test_generator_is_deterministic(config, tmp_path):
    engine = GeneratorEngine(config, tmp_path)
    engine.register("member", sample_member_generator)

    first_result = engine.run("member").read_bytes()
    second_result = engine.run("member").read_bytes()

    assert first_result == second_result


def test_unregistered_generator_fails(config, tmp_path):
    engine = GeneratorEngine(config, tmp_path)

    with pytest.raises(ValueError, match="No generator registered"):
        engine.run("member")


def test_disabled_dataset_fails(config, tmp_path):
    engine = GeneratorEngine(config, tmp_path)
    engine.register("claims", sample_member_generator)

    with pytest.raises(ValueError, match="disabled"):
        engine.run("claims")


def test_duplicate_registration_fails(config, tmp_path):
    engine = GeneratorEngine(config, tmp_path)
    engine.register("member", sample_member_generator)

    with pytest.raises(ValueError, match="already registered"):
        engine.register("member", sample_member_generator)


def test_unconfigured_dataset_fails(config, tmp_path):
    engine = GeneratorEngine(config, tmp_path)

    with pytest.raises(ValueError, match="not configured"):
        engine.register("unknown", sample_member_generator)


def test_generator_must_produce_file(config, tmp_path):
    def missing_file_generator(rng, output_dir, settings):
        return output_dir / "missing.csv"

    engine = GeneratorEngine(config, tmp_path)
    engine.register("member", missing_file_generator)

    with pytest.raises(RuntimeError, match="did not produce a file"):
        engine.run("member")


def test_generator_rejects_output_outside_directory(config, tmp_path):
    def outside_generator(rng, output_dir, settings):
        outside_file = output_dir.parent / "outside.csv"
        outside_file.write_text("test", encoding="utf-8")
        return outside_file

    engine = GeneratorEngine(config, tmp_path)
    engine.register("member", outside_generator)

    with pytest.raises(ValueError, match="inside its dataset directory"):
        engine.run("member")
