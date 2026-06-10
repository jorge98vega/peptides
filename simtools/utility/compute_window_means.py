#!/usr/bin/env python3
import os
import re
import argparse
import numpy as np


def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def extract_window_label(filename, prefix, suffix):
    name = os.path.basename(filename)
    if name.startswith(prefix) and name.endswith(suffix):
        return name[len(prefix): len(name) - len(suffix)]
    return name


def load_dump_file(path, cols, last=None):
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if last is not None:
        data = data[-last:]
    results = []
    for c in cols:
        if c > data.shape[1]:
            raise IndexError(f"column {c} out of range (file has {data.shape[1]} columns)")
        col_data = data[:, c - 1]
        results.append((col_data.mean(), col_data.std()))
    return results


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compute per-window mean and std from AMBER dump files. "
            "Columns are 1-indexed (col 1 = step, col 2 = first restraint, ...)."
        )
    )
    parser.add_argument("path", nargs="?", default=".",
                        help="Directory containing dump files (default: .)")
    parser.add_argument("--cols",   type=int, nargs="+", required=True,
                        help="1-indexed columns to compute (e.g. --cols 2 7); col 1 is the step counter")
    parser.add_argument("--last",   type=int, default=None,
                        help="Use only the last N rows per file (default: all)")
    parser.add_argument("--prefix", default="wham_",
                        help="Dump file name prefix (default: wham_)")
    parser.add_argument("--suffix", default="_rst_1.dump",
                        help="Dump file name suffix (default: _rst_1.dump)")
    parser.add_argument("--out",    default="window_means.dat",
                        help="Output file (default: window_means.dat)")
    args = parser.parse_args()

    if 1 in args.cols:
        print("Warning: col 1 is the simulation step counter, not a restraint value. "
              "Restraint 1 is col 2.")

    files = sorted(
        [f for f in os.listdir(args.path)
         if f.startswith(args.prefix) and f.endswith(args.suffix)],
        key=natural_sort_key
    )
    if not files:
        raise FileNotFoundError(
            f"No files matching '{args.prefix}*{args.suffix}' in '{args.path}'"
        )

    col_headers = []
    for c in args.cols:
        col_headers += [f"col{c}_mean", f"col{c}_std"]
    header = "# window " + " ".join(col_headers)

    rows = []
    for fn in files:
        fp    = os.path.join(args.path, fn)
        label = extract_window_label(fn, args.prefix, args.suffix)
        try:
            stats = load_dump_file(fp, args.cols, args.last)
            vals  = " ".join(f"{m:.6f} {s:.6f}" for m, s in stats)
            rows.append(f"{label} {vals}")
            print(f"  {fn}  ->  window {label:>6s}  " +
                  "  ".join(f"col{c}: {m:.4f} ± {s:.4f}"
                             for c, (m, s) in zip(args.cols, stats)))
        except Exception as e:
            print(f"Warning: skipping {fn}: {e}")

    with open(args.out, "w") as f:
        f.write(header + "\n")
        for row in rows:
            f.write(row + "\n")

    print(f"\nSaved: {args.out}  ({len(rows)} windows)")


if __name__ == "__main__":
    main()
