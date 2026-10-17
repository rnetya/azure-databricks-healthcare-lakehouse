"""Reusable execution engine for synthetic healthcare datasets."""

import logging
import random
from collections.abc import Callable
from pathlib import Path

from data_generation.config import get_output_directory

logger = logging.getLogger(__name__)

DatasetGenerator = Callable[[random.Random, Path, dict], Path]


class GeneratorEngine:
    """Register and execute synthetic dataset generators."""

    def __init__(self, config: dict, project_root: str | Path):
        self.config = config
        self.project_root = Path(project_root)
        self.registry: dict[str, DatasetGenerator] = {}

    def register(self, name: str, generator: DatasetGenerator) -> None:
        """Register a callable for a configured dataset."""
        if name not in self.config["datasets"]:
            raise ValueError(f"Dataset not configured: {name}")

        if name in self.registry:
            raise ValueError(f"Dataset already registered: {name}")

        self.registry[name] = generator

    def run(self, name: str) -> Path:
        """Execute a registered generator with a deterministic seed."""
        settings = self.config["datasets"].get(name)

        if settings is None:
            raise ValueError(f"Dataset not configured: {name}")

        if not settings["enabled"]:
            raise ValueError(f"Dataset is disabled: {name}")

        if name not in self.registry:
            raise ValueError(f"No generator registered for dataset: {name}")

        output_root = get_output_directory(self.config, self.project_root)
        dataset_output = output_root / name
        dataset_output.mkdir(parents=True, exist_ok=True)

        # Dataset-specific seed prevents execution order from
        # changing the random sequence of another dataset.
        seed_text = f"{self.config['random_seed']}:{name}"
        rng = random.Random(seed_text)

        logger.info("Starting dataset generation: %s", name)

        result = Path(self.registry[name](rng, dataset_output, settings))

        if not result.is_file():
            raise RuntimeError(f"Generator did not produce a file: {result}")

        if not result.resolve().is_relative_to(dataset_output.resolve()):
            raise ValueError("Generator output must remain inside its dataset directory.")

        logger.info("Completed dataset generation: %s -> %s", name, result)

        return result
