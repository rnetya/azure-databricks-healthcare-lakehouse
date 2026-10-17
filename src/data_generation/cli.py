"""Command-line interface for synthetic healthcare data generation."""

import argparse
import logging
from pathlib import Path

from data_generation.config import load_config
from data_generation.generator import GeneratorEngine
from data_generation.member import generate_member


def main(argv: list[str] | None = None) -> int:
    """Run the synthetic data generator CLI."""
    parser = argparse.ArgumentParser(description="Synthetic Healthcare Data Generator")

    parser.add_argument(
        "--config",
        default="config/generator.json",
        help="Path to generator configuration",
    )

    parser.add_argument(
        "--dataset",
        help="Name of the dataset to generate",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List configured datasets",
    )

    args = parser.parse_args(argv)

    if not args.list and not args.dataset:
        parser.error("Specify --list or --dataset NAME")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    config = load_config(args.config)

    if args.list:
        for name, settings in config["datasets"].items():
            status = "enabled" if settings["enabled"] else "disabled"
            print(f"{name}: {status} ({settings['format']})")
        return 0

    engine = GeneratorEngine(config, Path.cwd())

    # Register implemented dataset generators.
    engine.register(
        "member",
        lambda rng, output_dir, settings: generate_member(
            rng,
            output_dir,
            {
                **settings,
                "snapshot_date": config["snapshot_date"],
            },
        ),
    )

    # Validate requested dataset.
    if args.dataset not in config["datasets"]:
        parser.error(f"Unknown dataset: {args.dataset}")

    if not config["datasets"][args.dataset]["enabled"]:
        parser.error(f"Dataset is disabled: {args.dataset}")

    if args.dataset not in engine.registry:
        parser.error(f"Generator not yet implemented for dataset: {args.dataset}")

    # Execute registered generator.
    result = engine.run(args.dataset)

    print(f"Generated: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
