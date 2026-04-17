"""
Hardcoded benchmark grid → CSV + matplotlib figures in lab7/docs/results/.

Run from lab7/project after ``uv sync``::

  uv run python -m benchmarks.run_benchmarks
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from matrix_multiplication.registry import ALGOS
from plots.figures import plot_all

# --- Hardcoded experiment (edit here only) ---
# Full lab6-style sweep (slow): N_VALUES = list(range(100, 1001, 50)); NP_VALUES = list(range(2, 9)); RUNS = 10
N_VALUES = [100, 200, 400, 600, 800]
NP_VALUES = [2, 4, 6, 8]
RUNS = 5
MODES = list(ALGOS.keys())


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def lab7_root() -> Path:
    return Path(__file__).resolve().parents[2]


def results_dir() -> Path:
    return lab7_root() / "docs" / "results"


def bench_runner_path() -> Path:
    return project_root() / "benchmarks" / "bench_runner.py"


def run_one(mode: str, n: int, np_: int, cwd: Path) -> str:
    env = os.environ.copy()
    env["LAB7_MODE"] = mode
    env["LAB7_N"] = str(n)
    best_line: str | None = None
    best_sec: float | None = None
    runner = bench_runner_path()
    for _ in range(RUNS):
        proc = subprocess.run(
            ["mpirun", "-np", str(np_), sys.executable, str(runner)],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr or proc.stdout or f"mpirun failed ({proc.returncode})\n")
            raise subprocess.CalledProcessError(proc.returncode, proc.args)
        line = None
        for ln in proc.stdout.splitlines():
            ln = ln.strip()
            if ln.count(",") >= 5 and not ln.startswith("#"):
                parts = ln.split(",")
                if len(parts) >= 6 and parts[0] in ALGOS:
                    line = ln
                    break
        if not line:
            sys.stderr.write(f"No CSV line in output for mode={mode} np={np_} n={n}\n")
            sys.stderr.write(proc.stdout)
            raise RuntimeError("missing bench line")
        sec = float(line.split(",")[5])
        if best_sec is None or sec < best_sec:
            best_sec = sec
            best_line = line
    assert best_line is not None
    return best_line


def write_csv(rows: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("variant,nra,nca,ncb,procs,seconds\n")
        for r in rows:
            f.write(r + "\n")


def main() -> int:
    cwd = project_root()
    out_csv = results_dir() / "lab7_bench.csv"
    out_dir = results_dir()

    total = len(MODES) * len(NP_VALUES) * len(N_VALUES)
    done = 0
    lines: list[str] = []
    print(f"lab7 bench: {total} configurations (modes x np x N)", flush=True)
    for mode in MODES:
        for np_ in NP_VALUES:
            for n in N_VALUES:
                done += 1
                line = run_one(mode, n, np_, cwd)
                lines.append(line)
                if done % 20 == 0 or done == total:
                    print(f"  progress {done}/{total}", flush=True)

    write_csv(lines, out_csv)
    print(f"Wrote {out_csv}", flush=True)
    paths = plot_all(out_csv, out_dir, modes=MODES)
    for p in paths:
        print(f"Figure: {p}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
