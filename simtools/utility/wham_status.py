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


def display(grid_2d, list_1d, no_color):
    lines = []

    if grid_2d:
        rows = sorted(set(i for i, j in grid_2d))
        cols = sorted(set(j for i, j in grid_2d))
        rl = max(len(str(r)) for r in rows)
        pad = " " * (rl + 1)

        t, o = ruler(cols, pad)
        lines.append(t)
        lines.append(o)

        for i in rows:
            row = f"{i:>{rl}} "
            for j in cols:
                s = grid_2d.get((i, j), "none")
                row += nc(STATUS_SYM[s], s, no_color)
            lines.append(row)

        counts: dict[str, int] = defaultdict(int)
        for s in grid_2d.values():
            counts[s] += 1
        queued = sum(counts[s] for s in ("running", "dependency", "pending"))
        summary = f"\n{len(rows)}×{len(cols)} grid  |  in squeue: {queued}  "
        summary += "  ".join(
            f"{nc(STATUS_SYM[s], s, no_color)} {counts[s]}"
            for s in ("running", "dependency", "pending", "failed")
            if counts[s]
        )
        lines.append(summary)

    if list_1d:
        ks = sorted(list_1d)
        rl = max(len(str(k)) for k in ks)
        pad = " " * (rl + 1)
        t, o = ruler(ks, pad)
        lines.append("\n1D windows:")
        lines.append(t)
        lines.append(o)
        row = pad
        for k in ks:
            s = list_1d[k]
            row += nc(STATUS_SYM[s], s, no_color)
        lines.append(row)

        counts: dict[str, int] = defaultdict(int)
        for s in list_1d.values():
            counts[s] += 1
        lines.append("  ".join(
            f"{nc(STATUS_SYM[s], s, no_color)} {counts[s]}"
            for s in ("running", "dependency", "pending", "failed")
            if counts[s]
        ))

    lines.append("")
    legend = [("running", "R  running"), ("dependency", "D  dependency"),
              ("pending",  "P  pending (resources)"), ("failed", "F  failed"),
              ("done",     ".  completed/not in queue")]
    for s, label in legend:
        lines.append("  " + nc(STATUS_SYM[s], s, no_color) + "  " + label)

    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Visualize SLURM wham job grid")
    parser.add_argument("-u", "--user", default=os.environ.get("USER", ""),
                        help="SLURM user (default: $USER)")
    parser.add_argument("-p", "--prefix", default="wham_",
                        help="Job name prefix (default: wham_)")
    parser.add_argument("-W", "--watch", nargs="?", const=10, type=int, metavar="INTERVAL",
                        help="Refresh every INTERVAL seconds (default: 10)")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    def run_once():
        grid_2d, list_1d = query_jobs(args.user, args.prefix)
        if not grid_2d and not list_1d:
            print(f"No wham jobs found for user '{args.user}' with prefix '{args.prefix}'.")
            return False
        display(grid_2d, list_1d, args.no_color)
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
