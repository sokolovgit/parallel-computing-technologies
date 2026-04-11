"""
Lab 6 task 4: drive blocking / non-blocking matrix binaries via mpirun, write CSV.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_int_list(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def default_n_sizes() -> list[int]:
    return list(range(100, 1001, 50))


def default_np_list() -> list[int]:
    return list(range(2, 9))


def extract_bench_line(stdout: str) -> str | None:
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("blocking,") or line.startswith("nonblocking,"):
            return line
    return None


def run_mpirun_bench(bin_path: Path, np: int, n: int, runs: int, cwd: Path) -> str:
    best_line: str | None = None
    best_sec: float | None = None
    for _ in range(runs):
        proc = subprocess.run(
            ["mpirun", "-np", str(np), str(bin_path), str(n), str(n), str(n), "--bench"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr or proc.stdout or f"mpirun failed ({proc.returncode})\n")
            raise subprocess.CalledProcessError(proc.returncode, proc.args)
        line = extract_bench_line(proc.stdout)
        if not line:
            sys.stderr.write(f"No CSV line in mpirun output for {bin_path.name} np={np} n={n}\n")
            sys.stderr.write(proc.stdout)
            raise RuntimeError("missing bench line")
        parts = line.split(",")
        sec = float(parts[5])
        if best_sec is None or sec < best_sec:
            best_sec = sec
            best_line = line
    assert best_line is not None
    return best_line


def main() -> int:
    root = project_root()
    ap = argparse.ArgumentParser(description="MPI matrix multiply benchmark → CSV")
    ap.add_argument(
        "--out",
        default="results/lab6_bench.csv",
        help="output CSV path (relative to project root unless absolute)",
    )
    ap.add_argument(
        "--n",
        default=None,
        help="comma-separated N (square matrices). Default: 100,150,…,1000 (step 50)",
    )
    ap.add_argument(
        "--np",
        dest="np_list",
        default=None,
        help="comma-separated mpirun -np values. Default: 2,3,…,8",
    )
    ap.add_argument(
        "--runs",
        type=int,
        default=10,
        help="repeats per configuration; keep best (min) wall time (default: 10)",
    )
    ap.add_argument("--no-build", action="store_true", help="skip just build-task2 / build-task3")
    ap.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")
    args = ap.parse_args()

    sizes = parse_int_list(args.n) if args.n else default_n_sizes()
    nps = parse_int_list(args.np_list) if args.np_list else default_np_list()
    if args.runs < 1:
        ap.error("--runs must be >= 1")
    if not sizes or not nps:
        ap.error("sizes and np list must be non-empty")

    if not args.no_build:
        subprocess.run(["just", "build-task2"], cwd=root, check=True)
        subprocess.run(["just", "build-task3"], cwd=root, check=True)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    variants: list[tuple[str, Path]] = [
        ("blocking", root / "bin" / "task2_mm_blocking"),
        ("nonblocking", root / "bin" / "task3_mm_nonblocking"),
    ]
    for _, p in variants:
        if not p.is_file():
            sys.stderr.write(f"Missing binary: {p} (build first)\n")
            return 1

    total = len(variants) * len(nps) * len(sizes)
    idx = 0
    rows: list[str] = []
    for variant, bin_path in variants:
        for np in nps:
            for n in sizes:
                idx += 1
                if not args.quiet:
                    sys.stderr.write(f"[{idx}/{total}] {variant} np={np} n={n}\n")
                rows.append(run_mpirun_bench(bin_path, np, n, args.runs, root))

    with out_path.open("w", newline="", encoding="utf-8") as f:
        f.write("variant,nra,nca,ncb,procs,seconds\n")
        for line in rows:
            f.write(line + "\n")

    print(out_path.resolve())
    print(f"(best of {args.runs} run(s) per cell; {total} configurations)")
    return 0


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
