"""Entry point for running the benchmark as a module: python -m benchmark."""

import sys
from pathlib import Path

# Ensure src (bitonic package) is on path when running as __main__
_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from benchmark.runner import BenchmarkRunner

if __name__ == "__main__":
    BenchmarkRunner().run()
