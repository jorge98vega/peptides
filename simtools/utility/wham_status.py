#!/usr/bin/env python3
import subprocess
import sys
import os
import re
import time
import argparse
from collections import defaultdict
from datetime import datetime

RESET      = "\033[0m"
GREEN      = "\033[32m"
YELLOW     = "\033[33m"
CYAN       = "\033[36m"
RED        = "\033[31m"
DIM        = "\033[2m"
ORANGE     = "\033[38;5;214m"   # crashed: dump truncated (adjacent to missing)
ORANGE_RED = "\033[38;5;202m"   # missing: dump not found in dumps/

STATUS_COLOR = {
    "running":    GREEN,
    "dependency": YELLOW,
    "pending":    CYAN,
    "failed":     RED,
    "done":       DIM,
    "missing":    ORANGE_RED,
    "crashed":    ORANGE,
    "none":       "",
}
STATUS_SYM = {
    "running":    "R",
    "dependency": "D",
    "pending":    "P",
    "failed":     "F",
    "done":       ".",
    "missing":    ".",
    "crashed":    ".",
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


def dump_path(dumps_dir, prefix, i, j, dump_iter):
    if j is not None:
        fname = f"{prefix}{i}_{j}_rst_{dump_iter}.dump"
    else:
        fname = f"{prefix}{i}_rst_{dump_iter}.dump"
    return os.path.join(dumps_dir, fname)


def get_last_step(path):
    """Return last step number from a dump file by reading its tail."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return None
            f.seek(max(0, size - 512))
            tail = f.read().decode(errors="replace")
            for line in reversed(tail.splitlines()):
                line = line.strip()
                if line and not line.startswith("#"):
                    return int(float(line.split()[0]))
    except Exception:
        return None
    return None


def initial_status(squeue_status, has_dims, dumps_dir, path):
    """Resolve status for a window not currently in squeue."""
    if squeue_status is not None:
        return squeue_status
    if not has_dims:
        return "none"
    if dumps_dir and os.path.isdir(dumps_dir):
        return "done" if os.path.isfile(path) else "missing"
    return "done"


def mark_crashed(statuses, dumps_dir, prefix, dump_iter, nsteps, is_2d):
    """Upgrade 'done' windows adjacent to 'missing' ones to 'crashed' if dump is truncated."""
    missing = {k for k, v in statuses.items() if v == "missing"}
    if not missing:
        return
    for k, s in list(statuses.items()):
        if s != "done":
            continue
        if is_2d:
            i, j = k
            if (i, j - 1) not in missing and (i, j + 1) not in missing:
                continue
            p = dump_path(dumps_dir, prefix, i, j, dump_iter)
        else:
            if (k - 1) not in missing and (k + 1) not in missing:
                continue
            p = dump_path(dumps_dir, prefix, k, None, dump_iter)
        last = get_last_step(p)
        if last is not None and last < nsteps:
            statuses[k] = "crashed"


def generate_failed_windows(statuses, rows, cols, output_path):
    """Write failed_windows.dat: i j k, where k encodes direction of missing dumps."""
    cols_set = set(cols)
    entries = []
    for i in rows:
        for j in sorted(j for j in cols if statuses.get((i, j)) == "crashed"):
            left  = (j - 1) in cols_set and statuses.get((i, j - 1)) == "missing"
            right = (j + 1) in cols_set and statuses.get((i, j + 1)) == "missing"
            if left and right:
                k = 0
            elif right:
                k = 1
            elif left:
                k = -1
            else:
                continue
            entries.append((i, j, k))
    with open(output_path, "w") as f:
        for i, j, k in entries:
            f.write(f"{i} {j} {k}\n")
    return entries


def build_statuses_2d(grid_2d, rows, cols, has_dims, dumps_dir, prefix, dump_iter, nsteps):
    statuses = {}
    for i in rows:
        for j in cols:
            p = dump_path(dumps_dir, prefix, i, j, dump_iter) if dumps_dir else ""
            statuses[(i, j)] = initial_status(grid_2d.get((i, j)), has_dims, dumps_dir, p)
    if dumps_dir and os.path.isdir(dumps_dir):
        mark_crashed(statuses, dumps_dir, prefix, dump_iter, nsteps, is_2d=True)
    return statuses


def build_statuses_1d(list_1d, ks, has_dims, dumps_dir, prefix, dump_iter, nsteps):
    statuses = {}
    for k in ks:
        p = dump_path(dumps_dir, prefix, k, None, dump_iter) if dumps_dir else ""
        statuses[k] = initial_status(list_1d.get(k), has_dims, dumps_dir, p)
    if dumps_dir and os.path.isdir(dumps_dir):
        mark_crashed(statuses, dumps_dir, prefix, dump_iter, nsteps, is_2d=False)
    return statuses


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


def display(grid_2d, list_1d, no_color,
            rows_range=None, cols_range=None, windows_range=None,
            dumps_dir=None, prefix="wham_", dump_iter=1, nsteps=8000,
            failed_out=None):
    lines = []

    if grid_2d or rows_range:
        rows = rows_range if rows_range else sorted(set(i for i, j in grid_2d))
        cols = cols_range if cols_range else sorted(set(j for i, j in grid_2d))
        rl = max(len(str(r)) for r in rows)
        pad = " " * (rl + 1)

        statuses = build_statuses_2d(grid_2d, rows, cols, rows_range is not None,
                                     dumps_dir, prefix, dump_iter, nsteps)

        t, o = ruler(cols, pad)
        lines.append(t)
        lines.append(o)

        counts: dict[str, int] = defaultdict(int)
        for i in rows:
            row = f"{i:>{rl}} "
            for j in cols:
                s = statuses[(i, j)]
                counts[s] += 1
                row += nc(STATUS_SYM[s], s, no_color)
            lines.append(row)

        queued = sum(counts[s] for s in ("running", "dependency", "pending"))
        summary = (f"\n{len(rows)}×{len(cols)} grid  |  "
                   f"done: {counts['done']}  "
                   f"missing: {counts['missing']}  "
                   f"crashed: {counts['crashed']}  "
                   f"in squeue: {queued}  ")
        summary += "  ".join(
            f"{nc(STATUS_SYM[s], s, no_color)} {counts[s]}"
            for s in ("running", "dependency", "pending", "failed")
            if counts[s]
        )
        lines.append(summary)

        if failed_out and counts["crashed"]:
            entries = generate_failed_windows(statuses, rows, cols, failed_out)
            lines.append(f"  → wrote {len(entries)} entr{'y' if len(entries)==1 else 'ies'} to {failed_out}")

    if list_1d or windows_range:
        ks = windows_range if windows_range else sorted(list_1d)
        rl = max(len(str(k)) for k in ks)
        pad = " " * (rl + 1)

        statuses = build_statuses_1d(list_1d, ks, windows_range is not None,
                                     dumps_dir, prefix, dump_iter, nsteps)

        t, o = ruler(ks, pad)
        lines.append("\n1D windows:")
        lines.append(t)
        lines.append(o)
        row = pad
        counts: dict[str, int] = defaultdict(int)
        for k in ks:
            s = statuses[k]
            counts[s] += 1
            row += nc(STATUS_SYM[s], s, no_color)
        lines.append(row)

        queued = sum(counts[s] for s in ("running", "dependency", "pending"))
        lines.append(
            f"done: {counts['done']}  missing: {counts['missing']}  crashed: {counts['crashed']}  in squeue: {queued}  "
            + "  ".join(
                f"{nc(STATUS_SYM[s], s, no_color)} {counts[s]}"
                for s in ("running", "dependency", "pending", "failed")
                if counts[s]
            )
        )

    lines.append("")
    legend = [
        ("running",    "R  running"),
        ("dependency", "D  dependency"),
        ("pending",    "P  pending (resources)"),
        ("failed",     "F  failed"),
        ("done",       ".  done"),
        ("crashed",    ".  crashed  (dump truncated, adjacent to missing)"),
        ("missing",    ".  missing  (dump not in dumps/)"),
    ]
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
    parser.add_argument("-d", "--dumps", default="dumps",
                        help="Directory containing dump files (default: dumps)")
    parser.add_argument("--dump-iter", type=int, default=1, metavar="N",
                        help="Dump file iteration suffix (default: 1)")
    parser.add_argument("--nsteps", type=int, default=8000,
                        help="Expected simulation steps for crash detection (default: 8000)")
    parser.add_argument("-f", "--failed-out", default="failed_windows.dat", metavar="FILE",
                        help="Output file for crashed windows (default: failed_windows.dat)")
    parser.add_argument("-W", "--watch", nargs="?", const=10, type=int, metavar="INTERVAL",
                        help="Refresh every INTERVAL seconds (default: 10)")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    rows_range    = list(range(1, args.rows    + 1)) if args.rows    else None
    cols_range    = list(range(1, args.cols    + 1)) if args.cols    else None
    windows_range = list(range(1, args.windows + 1)) if args.windows else None

    def run_once():
        grid_2d, list_1d = query_jobs(args.user, args.prefix)
        if not grid_2d and not list_1d and not rows_range and not windows_range:
            print(f"No wham jobs found for user '{args.user}' with prefix '{args.prefix}'.")
            return False
        display(grid_2d, list_1d, args.no_color,
                rows_range=rows_range, cols_range=cols_range, windows_range=windows_range,
                dumps_dir=args.dumps, prefix=args.prefix,
                dump_iter=args.dump_iter, nsteps=args.nsteps,
                failed_out=args.failed_out)
        return True

    if args.watch is None:
        if not run_once():
            sys.exit(1)
    else:
        try:
            while True:
                print("\033[2J\033[H", end="")
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
