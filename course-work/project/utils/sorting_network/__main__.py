import argparse
import sys

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
    args = parser.parse_args()

    n = args.n
    title = args.title or f"Bitonic sort, n={n}"

    if args.text:
        stages = bitonic_stages(n)
        print(format_stages(stages, n, title=title))
        return 0

    network = build_bitonic_network(n)
    stages = bitonic_stages(n)
    svg = render_svg(network, title=title, stages=stages)

    if args.output:
        with open(args.output, "w") as f:
            f.write(svg)
    else:
        print(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
