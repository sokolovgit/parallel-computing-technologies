from __future__ import annotations

import json
import sys
from pathlib import Path


def load_result(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def recommend_from_data(data: dict) -> list[tuple[int, int, float, float]]:
    speedup = data.get("speedup") or {}
    efficiency = data.get("efficiency") or {}
    if not speedup:
        return []
    sizes = sorted(
        {int(s) for np_ in speedup for s in speedup[str(np_)]},
        key=int,
    )
    nprocs_list = sorted(int(np_) for np_ in speedup)
    out: list[tuple[int, int, float, float]] = []
    for size in sizes:
        best_p = nprocs_list[0]
        best_sp = 0.0
        for np_ in nprocs_list:
            sp = speedup.get(str(np_), {}).get(str(size), 0.0)
            if sp > best_sp:
                best_sp = sp
                best_p = np_
        eff = efficiency.get(str(best_p), {}).get(str(size), 0.0)
        out.append((size, best_p, best_sp, eff))
    return out


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    default_path = root / "results" / "benchmark_data.json"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    data = load_result(path)
    rows = recommend_from_data(data)
    if not rows:
        print("No speedup data in JSON.", file=sys.stderr)
        return 1
    print("Recommended process count per size (by best speedup):")
    print(f"{'Size':>12}  {'P':>4}  {'Speedup':>10}  {'Efficiency':>10}")
    print("-" * 42)
    for size, p, sp, eff in rows:
        print(f"{size:>12,}  {p:>4}  {sp:>10.3f}  {eff:>10.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
