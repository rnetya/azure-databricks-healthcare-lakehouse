"""Configuration loading and validation for synthetic data generation."""

import json
from pathlib import Path


def load_config(config_path: str | Path = "config/generator.json") -> dict:
    """Load and validate generator configuration."""
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Generator configuration not found: {path}")

    with path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Generator configuration must be a JSON object.")

    required_fields = ("project", "environment", "random_seed", "output_directory", "datasets")

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")

    if not isinstance(config["random_seed"], int) or isinstance(config["random_seed"], bool):
        raise ValueError("random_seed must be an integer.")

    if not isinstance(config["output_directory"], str) or not config["output_directory"].strip():
        raise ValueError("output_directory must be a non-empty string.")

    if not isinstance(config["datasets"], dict) or not config["datasets"]:
        raise ValueError("datasets must be a non-empty object.")

    for dataset_name, dataset_settings in config["datasets"].items():
        if not isinstance(dataset_settings, dict):
            raise ValueError(f"Invalid configuration for dataset: {dataset_name}")

        if not isinstance(dataset_settings.get("enabled"), bool):
            raise ValueError(f"Dataset {dataset_name} must have a boolean enabled setting.")

        if not isinstance(dataset_settings.get("format"), str):
            raise ValueError(f"Dataset {dataset_name} must specify a format.")

        if "record_count" in dataset_settings:
            count = dataset_settings["record_count"]
            if type(count) is not int or count <= 0:
                raise ValueError(f"Dataset {dataset_name} must have a positive record_count.")

    return config


def get_output_directory(config: dict, project_root: str | Path) -> Path:
    """Resolve and create the configured local output directory."""
    root = Path(project_root).resolve()
    output = (root / config["output_directory"]).resolve()

    if not output.is_relative_to(root):
        raise ValueError("Output directory must remain inside the project root.")

    output.mkdir(parents=True, exist_ok=True)
    return output
