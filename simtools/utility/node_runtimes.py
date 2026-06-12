#!/usr/bin/env python3
"""Report run times per node for wham windows.

Usage:
    python node_runtimes.py <windows_dir>

For each wham_i_j directory, picks the SLURM job with the longest wall time
(the one that completed the full simulation), extracts the compute node from
the .out file, and prints a summary sorted by node.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict


def parse_clock(clock_file):
    """Return total seconds from D/H/M/S line, or None if not found."""
    pattern = re.compile(r'D/H/M/S:\s+(\d+):(\d+):(\d+):(\d+)')
    for line in clock_file.read_text().splitlines():
        m = pattern.search(line)
        if m:
            d, h, mn, s = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            return d * 86400 + h * 3600 + mn * 60 + s
    return None


def parse_node(out_file):
    """Return node integer from 'Machine name: compute-0-N.local', or None."""
    pattern = re.compile(r'Machine name:\s+compute-0-(\d+)\.local')
    for line in out_file.read_text().splitlines():
        m = pattern.search(line)
        if m:
            return int(m.group(1))
    return None


def seconds_to_dhms(secs):
    d = secs // 86400
    secs %= 86400
    h = secs // 3600
    secs %= 3600
    mn = secs // 60
    s = secs % 60
    return f"{d:02d}:{h:02d}:{mn:02d}:{s:02d}"


def main(windows_dir):
    windows_dir = Path(windows_dir)
    wham_dirs = sorted(windows_dir.glob("wham_*_*"))

    results = []  # (i, j, node, total_seconds)

    for wdir in wham_dirs:
        name = wdir.name  # e.g. wham_10_1
        parts = name.split('_')
        if len(parts) != 3:
            continue
        i, j = int(parts[1]), int(parts[2])

        clock_files = list(wdir.glob("slurm-*.clock"))
        if not clock_files:
            continue

        # Pick the SLURM ID with the highest wall time
        best_id = None
        best_secs = -1
        for cf in clock_files:
            secs = parse_clock(cf)
            if secs is not None and secs > best_secs:
                best_secs = secs
                best_id = cf.stem  # e.g. slurm-1229308

        if best_id is None:
            continue

        out_file = wdir / f"{best_id}.out"
        node = parse_node(out_file) if out_file.exists() else None

        results.append((i, j, node, best_secs))

    if not results:
        print("No results found.")
        return

    # --- Per-node summary ---
    node_data = defaultdict(list)
    for _, _, node, secs in results:
        node_data[node].append(secs)

    print(f"{'Node':>6} {'Windows':>8} {'Mean D:H:M:S':>14} {'Min D:H:M:S':>14} {'Max D:H:M:S':>14}")
    print("-" * 62)
    for node in sorted(node_data):
        times = node_data[node]
        mean_s = sum(times) // len(times)
        node_str = str(node) if node is not None else "?"
        print(f"{node_str:>6} {len(times):>8} {seconds_to_dhms(mean_s):>14} "
              f"{seconds_to_dhms(min(times)):>14} {seconds_to_dhms(max(times)):>14}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <windows_dir>")
        sys.exit(1)
    main(sys.argv[1])
