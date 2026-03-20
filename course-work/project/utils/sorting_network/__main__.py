import argparse
import sys
from pathlib import Path

from .bitonic import bitonic_stages, build_bitonic_network
from .svg import render_svg
from .view import format_stages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate bitonic sort network (SVG or text view)"
    )
    parser.add_argument(
        "n",
        type=int,
        help="Number of wires (power of 2, e.g. 4, 8, 16)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="",
        help="Output file (default: stdout); ignored if --text",
    )
    parser.add_argument(
        "--title",
        default="",
        help="Title (default: 'Bitonic sort, n=<n>')",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Print algorithm stages as text (no SVG)",
    )
    parser.add_argument(
        "--processes",
        "-p",
        type=int,
        default=0,
        metavar="P",
        help="Show work distribution over P processes (colors in SVG, P0/P1 in text)",
    )
    parser.add_argument(
        "--highlight-independent",
        action="store_true",
        help="Highlight each stage as an independent parallel phase in SVG output",
    )
    args = parser.parse_args()

    n = args.n
    title = args.title or f"Bitonic sort, n={n}"
    processes = args.processes if args.processes > 0 else None

    if args.text:
        stages = bitonic_stages(n)
        print(format_stages(stages, n, title=title, processes=processes))
        return 0

    network = build_bitonic_network(n)
    stages = bitonic_stages(n)
    svg = render_svg(
        network,
        title=title,
        stages=stages,
        processes=processes,
        highlight_independent=args.highlight_independent,
    )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg, encoding="utf-8")
    else:
        print(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
