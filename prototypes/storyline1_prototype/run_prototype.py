#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the Storyline 1 Interpreted Report Prototype.

Usage:
    python -m prototypes.storyline1_prototype.run_prototype --input storyline1_pipeline/test_run2
    python -m prototypes.storyline1_prototype.run_prototype --input storyline1_pipeline/test_run2 --output prototypes/storyline1_prototype/output
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from prototypes.storyline1_prototype.report_interpreted import generate_interpreted_report


def main():
    parser = argparse.ArgumentParser(
        description="Generate Storyline 1 Interpreted Report Prototype"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to Storyline 1 output directory (must contain tables/ and figures/)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: prototypes/storyline1_prototype/output/)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else (project_root / "prototypes" / "storyline1_prototype" / "output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "storyline1_interpreted.html"

    print(f"[INPUT]  {input_dir.resolve()}")
    print(f"[OUTPUT] {output_file.resolve()}")
    print()

    html = generate_interpreted_report(str(input_dir))

    output_file.write_text(html, encoding="utf-8")
    print(f"[OK] Report generated: {output_file.resolve()}")
    print(f"     Size: {output_file.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
