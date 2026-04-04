#!/usr/bin/env python3
"""
Download public-domain plain text and split into many files under a nested directory tree
for ForkJoin / I/O heavy benchmarks (lab4).

Uses urllib only (no requests). Respects Project Gutenberg by identifying downloads with a
clear User-Agent. Sources are UTF-8 text; binary or unknown encodings are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path


# Stable Gutenberg UTF-8 mirrors (plain .txt); small set to avoid hammering the site.
DEFAULT_SOURCES: list[tuple[str, str]] = [
    ("gutenberg_pride_prejudice", "https://www.gutenberg.org/files/1342/1342-0.txt"),
    ("gutenberg_moby_dick", "https://www.gutenberg.org/files/2701/2701-0.txt"),
    ("gutenberg_sherlock", "https://www.gutenberg.org/files/1661/1661-0.txt"),
    ("gutenberg_alice", "https://www.gutenberg.org/files/11/11-0.txt"),
    ("gutenberg_frankenstein", "https://www.gutenberg.org/files/84/84-0.txt"),
]


def fetch(url: str, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "lab4-corpus-fetch/1.0 (student benchmark; +https://www.gutenberg.org/policy/robot_access)",
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def nested_path(out_root: Path, source_id: str, shard: int, seq: int, depth: int) -> Path:
    """
    Build a non-flat path: out_root / lane_a / lane_b / source / shard_XX / seg_XXXXX.txt
    depth controls how many hashed subfolders are inserted.
    """
    h = hashlib.sha1(source_id.encode("utf-8")).hexdigest()
    parts: list[str] = []
    for d in range(max(1, depth)):
        parts.append(f"bucket_{h[d * 2 : d * 2 + 2]}")
    parts.append(source_id)
    parts.append(f"shard_{shard:02d}")
    return out_root.joinpath(*parts) / f"seg_{seq:05d}.txt"


def write_chunks(
    text: str,
    out_root: Path,
    source_id: str,
    per_file_chars: int,
    depth: int,
) -> int:
    n = len(text)
    if n == 0:
        return 0
    num_files = max(1, math.ceil(n / per_file_chars))
    shards = max(1, int(math.sqrt(num_files)))
    written = 0
    for i in range(num_files):
        chunk = text[i * per_file_chars : (i + 1) * per_file_chars]
        if not chunk.strip():
            continue
        shard = i % shards
        path = nested_path(out_root, source_id, shard, i, depth)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(chunk, encoding="utf-8", newline="\n")
        written += 1
    return written


def main() -> None:
    p = argparse.ArgumentParser(description="Download texts and write nested corpus .txt files")
    p.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="Project root (parent of data/); corpus written to data/corpus/",
    )
    p.add_argument(
        "--out-subdir",
        type=str,
        default="data/corpus",
        help="Relative to base-dir",
    )
    p.add_argument("--per-file-kb", type=int, default=256, help="Approx max UTF-8 size per file (KB)")
    p.add_argument("--nest-depth", type=int, default=3, help="Number of hashed directory levels")
    p.add_argument(
        "--max-total-mb",
        type=int,
        default=80,
        help="Stop fetching more books after stored raw text reaches this many MB (approx)",
    )
    p.add_argument("--sleep", type=float, default=1.5, help="Pause between HTTP downloads (seconds)")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned layout without downloading",
    )
    args = p.parse_args()

    out_root = (args.base_dir / args.out_subdir).resolve()
    per_file_chars = max(4096, args.per_file_kb * 1024)

    if args.dry_run:
        demo = nested_path(out_root, "demo_source", shard=3, seq=42, depth=args.nest_depth)
        print("Dry run — example path:", demo)
        print("Out root:", out_root)
        return

    out_root.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    max_bytes = args.max_total_mb * 1024 * 1024
    files_written = 0

    for sid, url in DEFAULT_SOURCES:
        if total_bytes >= max_bytes:
            break
        print(f"Fetching {sid} …")
        try:
            raw = fetch(url)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  skip {url}: {e}")
            time.sleep(args.sleep)
            continue
        total_bytes += len(raw)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        n = write_chunks(text, out_root, sid, per_file_chars, args.nest_depth)
        files_written += n
        print(f"  wrote {n} files under {out_root}")
        time.sleep(args.sleep)

    print(f"Done. Total downloaded ~{total_bytes / (1024 * 1024):.2f} MiB, {files_written} segment files.")


if __name__ == "__main__":
    main()
