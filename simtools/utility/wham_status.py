#!/usr/bin/env python3
import subprocess
import sys
import os
import re
import time
import argparse
from collections import defaultdict
from datetime import datetime

RESET  = "\033[0m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"
DIM    = "\033[2m"

STATUS_COLOR = {
    "running":    GREEN,
    "dependency": YELLOW,
    "pending":    CYAN,
    "failed":     RED,
    "done":       DIM,
    "none":       "",
}
STATUS_SYM = {
    "running":    "R",
    "dependency": "D",
    "pending":    "P",
    "failed":     "F",
    "done":       ".",
    "none":       " ",
}


def classify(state, reason):
    if state == "RUNNING":
        return "running"
    if state == "PENDING" and "Dependency" in reason:
        return "dependency"
    if state == "PENDING":
        return "pending"
    if state in ("FAILED", "TIMEOUT", "CANCELLED"):
        return "failed"
    if state == "COMPLETED":
        return "done"
    return "none"


def nc(text, status, no_color):
    c = STATUS_COLOR[status]
    if no_color or not c:
        return text
    return f"{c}{text}{RESET}"


def ruler(cols, pad):
    tens = pad + "".join(str(j // 10) if j % 10 == 0 else " " for j in cols)
    ones = pad + "".join(str(j % 10) for j in cols)
    return tens, ones


def query_jobs(user, prefix):
    cmd = ["squeue", f"--user={user}", "--format=%i|%500j|%T|%r", "--noheader"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    pat_2d = re.compile(r"^" + re.escape(prefix) + r"(\d+)_(\d+)$")
    pat_1d = re.compile(r"^" + re.escape(prefix) + r"(\d+)$")

    grid_2d: dict[tuple[int, int], str] = {}
    list_1d: dict[int, str] = {}

    for line in result.stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 4:
            continue
        _, name, state, reason = parts[0], parts[1].strip(), parts[2].strip(), parts[3].strip()
        if not name.startswith(prefix):
            continue
        status = classify(state, reason)
        m = pat_2d.match(name)
        if m:
            grid_2d[(int(m.group(1)), int(m.group(2)))] = status
            continue
        m = pat_1d.match(name)
        if m:
            list_1d[int(m.group(1))] = status

    return grid_2d, list_1d


def display(grid_2d, list_1d, no_color, rows_range=None, cols_range=None, windows_range=None):
    lines = []

    if grid_2d or rows_range:
        rows = rows_range if rows_range else sorted(set(i for i, j in grid_2d))
        cols = cols_range if cols_range else sorted(set(j for i, j in grid_2d))
        rl = max(len(str(r)) for r in rows)
        pad = " " * (rl + 1)

        t, o = ruler(cols, pad)
        lines.append(t)
        lines.append(o)

        counts: dict[str, int] = defaultdict(int)
        for i in rows:
            row = f"{i:>{rl}} "
            for j in cols:
                s = grid_2d.get((i, j), "done" if rows_range else "none")
                counts[s] += 1
                row += nc(STATUS_SYM[s], s, no_color)
            lines.append(row)

        queued = sum(counts[s] for s in ("running", "dependency", "pending"))
        done = counts["done"]
        summary = f"\n{len(rows)}×{len(cols)} grid  |  done: {done}  in squeue: {queued}  "
        summary += "  ".join(
            f"{nc(STATUS_SYM[s], s, no_color)} {counts[s]}"
            for s in ("running", "dependency", "pending", "failed")
            if counts[s]
        )
        lines.append(summary)

    if list_1d or windows_range:
        ks = windows_range if windows_range else sorted(list_1d)
        rl = max(len(str(k)) for k in ks)
        pad = " " * (rl + 1)
        t, o = ruler(ks, pad)
        lines.append("\n1D windows:")
        lines.append(t)
        lines.append(o)
        row = pad
        counts: dict[str, int] = defaultdict(int)
        for k in ks:
            s = list_1d.get(k, "done" if windows_range else "none")
            counts[s] += 1
            row += nc(STATUS_SYM[s], s, no_color)
        lines.append(row)

        done = counts["done"]
        queued = sum(counts[s] for s in ("running", "dependency", "pending"))
        lines.append(f"done: {done}  in squeue: {queued}  " + "  ".join(
            f"{nc(STATUS_SYM[s], s, no_color)} {counts[s]}"
            for s in ("running", "dependency", "pending", "failed")
            if counts[s]
        ))

    lines.append("")
    legend = [("running", "R  running"), ("dependency", "D  dependency"),
              ("pending",  "P  pending (resources)"), ("failed", "F  failed"),
              ("done",     ".  done / not in squeue")]
    for s, label in legend:
        lines.append("  " + nc(STATUS_SYM[s], s, no_color) + "  " + label)

    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Visualize SLURM wham job grid")
    parser.add_argument("-u", "--user", default=os.environ.get("USER", ""),
                        help="SLURM user (default: $USER)")
    parser.add_argument("-p", "--prefix", default="wham_",
                        help="Job name prefix (default: wham_)")
    parser.add_argument("-r", "--rows", type=int, metavar="N",
                        help="Total number of axis-1 (row) windows in the 2D grid")
    parser.add_argument("-c", "--cols", type=int, metavar="N",
                        help="Total number of axis-2 (col) windows in the 2D grid")
    parser.add_argument("-n", "--windows", type=int, metavar="N",
                        help="Total number of 1D windows")
    parser.add_argument("-W", "--watch", nargs="?", const=10, type=int, metavar="INTERVAL",
                        help="Refresh every INTERVAL seconds (default: 10)")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    rows_range   = list(range(1, args.rows    + 1)) if args.rows    else None
    cols_range   = list(range(1, args.cols    + 1)) if args.cols    else None
    windows_range = list(range(1, args.windows + 1)) if args.windows else None

    def run_once():
        grid_2d, list_1d = query_jobs(args.user, args.prefix)
        if not grid_2d and not list_1d and not rows_range and not windows_range:
            print(f"No wham jobs found for user '{args.user}' with prefix '{args.prefix}'.")
            return False
        display(grid_2d, list_1d, args.no_color,
                rows_range=rows_range, cols_range=cols_range, windows_range=windows_range)
        return True

    if args.watch is None:
        if not run_once():
            sys.exit(1)
    else:
        try:
            while True:
                print("\033[2J\033[H", end="")  # clear screen, move cursor home
                print(f"wham_status  —  every {args.watch}s  —  {datetime.now().strftime('%H:%M:%S')}  (Ctrl+C to quit)\n")
                try:
                    run_once()
                except RuntimeError as e:
                    print(f"squeue error: {e}", file=sys.stderr)
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
