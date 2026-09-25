from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .config import GeneratorConfig
from .main import generate_dataset


def _small_cfg(output: Path, seed: int) -> GeneratorConfig:
    return GeneratorConfig(
        seed=seed,
        output_dir=output,
        n_customers=2_000,
        n_restaurants=20,
        n_categories=10,
        n_menu_items=150,
        n_promotions=30,
        n_orders=5_000,
        n_ratings=50_000,
        n_wastage=20_000,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true",
                        help="Run a smaller smoke dataset.")
    parser.add_argument("--out", type=str, default=None,
                        help="Override output directory.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.test:
        output = Path(args.out or "smoke_output")
        cfg = _small_cfg(output, args.seed)
    else:
        output = Path(args.out or "full_output")
        cfg = GeneratorConfig(seed=args.seed, output_dir=output)

    if args.out:
        cfg = replace(cfg, output_dir=Path(args.out))

    tables, validation = generate_dataset(cfg, run_validation_flag=True)

    if validation and not validation["passed"]:
        fails = [c for c in validation["checks"] if not c["passed"]]
        print(f"\n{len(fails)} FAILED CHECKS")
        raise SystemExit(1)


if __name__ == "__main__":
    main()