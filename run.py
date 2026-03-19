"""
Run this script to execute your full pipeline and view results.

Usage:
    python run.py              # Render top 5, save to output/
    python run.py --top 10     # Render top 10
    python run.py --all        # Render all 20

Output images will be saved to the output/ directory.
"""

import argparse
import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.main import render_top_n, find_all_results


def main():
    parser = argparse.ArgumentParser(description="Equipment Placement — Run Pipeline")
    parser.add_argument("--top", type=int, default=5, help="Number of top results to render (default: 5)")
    parser.add_argument("--all", action="store_true", help="Render all 20 floor plans")
    parser.add_argument("--output", type=str, default="output", help="Output directory (default: output/)")
    args = parser.parse_args()

    n = 20 if args.all else args.top

    print(f"Processing all 20 floor plans...\n")

    paths = render_top_n(n=n, output_dir=args.output)

    print(f"\n{'='*52}")
    print(f"Rendered {len(paths)} annotated floor plans to {args.output}/")
    print(f"\nFiles:")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
