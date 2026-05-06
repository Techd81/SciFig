"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .api import plot
from .registry import get_chart_info, list_charts
from .styles import available_profiles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scifig", description="Generate publication-ready scientific figures.")
    sub = parser.add_subparsers(dest="command")

    plot_parser = sub.add_parser("plot", help="Generate a figure from a data file.")
    plot_parser.add_argument("data")
    plot_parser.add_argument("--chart", default="auto")
    plot_parser.add_argument("--style", default="nature", choices=available_profiles())
    plot_parser.add_argument("--palette", default="colorblind")
    plot_parser.add_argument("--stats", default="strict", choices=["strict", "standard", "descriptive", "none"])
    plot_parser.add_argument("--dpi", type=int, default=300)
    plot_parser.add_argument("-o", "--output", required=True)

    sub.add_parser("list-charts", help="List available chart types.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "list-charts":
        for key in list_charts():
            info = get_chart_info(key)
            print(f"{key}\t{info['category']}\t{info['description']}")
        return 0
    if args.command == "plot":
        try:
            plot(args.data, chart=args.chart, style=args.style, palette=args.palette,
                 output=args.output, stats=args.stats, dpi=args.dpi)
            return 0
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Rendering failed: {exc}", file=sys.stderr)
            return 2
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
