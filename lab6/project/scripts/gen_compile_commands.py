#!/usr/bin/env python3
"""Write lab6/project/compile_commands.json for clangd using mpicc -showme:compile."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    mpicc = shutil.which("mpicc")
    if not mpicc:
        print("mpicc not found; install Open MPI (e.g. brew install open-mpi)", file=sys.stderr)
        return 1
    try:
        show = subprocess.check_output([mpicc, "-showme:compile"], text=True).strip()
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        return 1
    mpi_cflags = show.split()
    common = ["-O2", "-Wall", "-Wextra", "-std=c11"] + mpi_cflags
    src_dir = root / "src"
    files = sorted(src_dir.glob("*.c"))
    if not files:
        print(f"No sources under {src_dir}", file=sys.stderr)
        return 1

    out_path = root / "compile_commands.json"
    entries: list[dict[str, object]] = []
    for f in files:
        args = [mpicc] + common + ["-c", str(f.resolve())]
        entries.append(
            {
                "directory": str(root),
                "arguments": args,
                "file": str(f.resolve()),
            }
        )

    out_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(out_path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
