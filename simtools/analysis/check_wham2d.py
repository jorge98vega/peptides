#!/usr/bin/env python3
"""
check_wham2d.py — quality check for 2D WHAM dump files.

For each (i, j) window computes means over the last --last rows and builds
three heatmaps:
  - |mean_col1 - target1|  (restrained coord 1 deviation)
  - |mean_col2 - target2|  (restrained coord 2 deviation)
  - max z-score across non-restrained columns  (geometry anomaly)

Optionally flags windows above threshold and writes failed_windows.dat.
"""

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap


def dump_path(dumps_dir, prefix, i, j, dump_iter):
    return os.path.join(dumps_dir, f"{prefix}{i}_{j}_rst_{dump_iter}.dump")


def load_means(dumps_dir, prefix, rows, cols, dump_iter, last):
    means = {}
    for i in rows:
        for j in cols:
            p = dump_path(dumps_dir, prefix, i, j, dump_iter)
            if not os.path.isfile(p):
                means[(i, j)] = None
                continue
            try:
                data = np.loadtxt(p)
                if data.ndim == 1:
                    data = data.reshape(1, -1)
                if last is not None and last < len(data):
                    data = data[-last:]
                means[(i, j)] = data.mean(axis=0)
            except Exception:
                means[(i, j)] = None
    return means


def to_matrix(rows, cols, value_dict):
    mat = np.full((len(rows), len(cols)), np.nan)
    for ri, i in enumerate(rows):
        for ci, j in enumerate(cols):
            v = value_dict.get((i, j))
            if v is not None and not np.isnan(v):
                mat[ri, ci] = v
    return mat



def write_failed_windows(flagged_or_missing, rows, cols, output_path):
    """Write one entry per contiguous chain of flagged windows per row.

    A single chain starting at j_min with direction=next is enough:
    run_all_wham2d.sh cascades through the rest automatically.
    Isolated single windows get direction=none.
    """
    entries = []
    cols_set = set(cols)
    for i in rows:
        flagged_js = sorted(j for j in cols_set if (i, j) in flagged_or_missing)
        if not flagged_js:
            continue
        # Group into contiguous chains
        chains, chain = [], [flagged_js[0]]
        for j in flagged_js[1:]:
            if j == chain[-1] + 1:
                chain.append(j)
            else:
                chains.append(chain)
                chain = [j]
        chains.append(chain)

        for chain in chains:
            if len(chain) == 1:
                entries.append((i, chain[0], "none"))
            else:
                left_good  = (chain[0]  - 1) in cols_set and (i, chain[0]  - 1) not in flagged_or_missing
                right_good = (chain[-1] + 1) in cols_set and (i, chain[-1] + 1) not in flagged_or_missing
                if left_good:
                    entries.append((i, chain[0],  "next"))
                elif right_good:
                    entries.append((i, chain[-1], "prev"))
                else:
                    entries.append((i, chain[0],  "next"))  # full-span chain, fall back

    with open(output_path, "w") as f:
        for i, j, direction in entries:
            f.write(f"{i} {j} {direction}\n")
    return entries


def main():
    parser = argparse.ArgumentParser(description="Quality check heatmaps for 2D WHAM dump files")
    parser.add_argument("--dumps",             default="dumps",
                        help="Dumps directory (default: dumps)")
    parser.add_argument("--prefix",            default="wham_",
                        help="Dump file prefix (default: wham_)")
    parser.add_argument("--rows",              type=int, required=True,
                        help="Number of axis-1 (fixed coord) windows")
    parser.add_argument("--cols",              type=int, required=True,
                        help="Number of axis-2 (free coord) windows")
    parser.add_argument("--rst-cols",          type=int, nargs=2, required=True, metavar=("COL1", "COL2"),
                        help="1-indexed columns for the two restrained coordinates in the dump file")
    parser.add_argument("--free-cols",         type=int, nargs="+", metavar="COL",
                        help="1-indexed columns to use as non-restrained (default: all non-restrained)")
    parser.add_argument("--start1",            type=float, required=True,
                        help="Target center for col1 at row i=1")
    parser.add_argument("--step1",             type=float, required=True,
                        help="Target step per row for col1")
    parser.add_argument("--start2",            type=float, required=True,
                        help="Target center for col2 at col j=1")
    parser.add_argument("--step2",             type=float, required=True,
                        help="Target step per col for col2")
    parser.add_argument("--last",              type=int,   default=None,
                        help="Use last N rows of each dump (default: all)")
    parser.add_argument("--dump-iter",         type=int,   default=1,
                        help="Dump file iteration suffix (default: 1)")
    parser.add_argument("--threshold",         type=float, default=None,
                        help="Flag windows where restrained deviation exceeds this value")
    parser.add_argument("--anomaly-threshold", type=float, default=None,
                        help="Flag windows where non-restrained z-score exceeds this value")
    parser.add_argument("--failed-out",        default="failed_windows.dat",
                        help="Output file for flagged windows (default: failed_windows.dat)")
    parser.add_argument("--save",              default=None,
                        help="Save figure to this path")
    parser.add_argument("--save-data",         default=None, metavar="FILE",
                        help="Save per-window scores to a text file (i j dev1 dev2 anomaly anomaly_col)")
    args = parser.parse_args()

    rows = list(range(1, args.rows + 1))
    cols = list(range(1, args.cols + 1))
    c1 = args.rst_cols[0] - 1  # 0-indexed
    c2 = args.rst_cols[1] - 1

    print(f"Loading {len(rows)}x{len(cols)} windows from {args.dumps} ...")
    means = load_means(args.dumps, args.prefix, rows, cols, args.dump_iter, args.last)
    n_loaded = sum(1 for v in means.values() if v is not None)
    print(f"  {n_loaded}/{len(rows)*len(cols)} dump files found")

    n_dump_cols = next((len(v) for v in means.values() if v is not None), None)
    if n_dump_cols is None:
        print("No dump files found.")
        sys.exit(1)

    # Columns that are not step (col 0) and not restrained
    if args.free_cols:
        free_col_indices = [c - 1 for c in args.free_cols if (c - 1) not in (c1, c2)]
    else:
        free_col_indices = [c for c in range(1, n_dump_cols) if c not in (c1, c2)]

    # --- Restrained coord deviations ---
    dev1, dev2 = {}, {}
    for i in rows:
        for j in cols:
            v = means[(i, j)]
            t1 = args.start1 + (i - 1) * args.step1
            t2 = args.start2 + (j - 1) * args.step2
            dev1[(i, j)] = abs(v[c1] - t1) if v is not None else np.nan
            dev2[(i, j)] = abs(v[c2] - t2) if v is not None else np.nan

    mat1 = to_matrix(rows, cols, dev1)
    mat2 = to_matrix(rows, cols, dev2)

    # --- Non-restrained anomaly score (mean z-score across free columns) ---
    # Mean z aggregates the correlated signal when bad geometry shifts many coords
    # simultaneously; max would let a single high-variance column dominate.
    anomaly     = {k: (0.0  if v is not None else np.nan) for k, v in means.items()}
    anomaly_col = {k: (None if v is not None else None)   for k, v in means.items()}
    n_free      = {k: 0 for k in means}
    max_z_track = {k: 0.0 for k in means}
    for c in free_col_indices:
        vals = np.array([means[k][c] for k in means if means[k] is not None])
        if len(vals) < 2:
            continue
        gstd = vals.std()
        if gstd < 1e-10:
            continue
        gmed = np.median(vals)
        for k, v in means.items():
            if v is None:
                continue
            z = abs(v[c] - gmed) / gstd
            anomaly[k] += z
            n_free[k]  += 1
            if z > max_z_track[k]:
                max_z_track[k] = z
                anomaly_col[k] = c + 1  # 1-indexed col with highest individual z

    for k in means:
        if means[k] is not None and n_free[k] > 0:
            anomaly[k] /= n_free[k]

    mat_anomaly = to_matrix(rows, cols, anomaly)

    # --- Save numerical data ---
    if args.save_data:
        with open(args.save_data, "w") as f:
            f.write("# i  j  dev_col1  dev_col2  anomaly_zscore  anomaly_col\n")
            for i in rows:
                for j in cols:
                    k = (i, j)
                    d1 = dev1[k]
                    d2 = dev2[k]
                    an = anomaly[k]
                    ac = anomaly_col[k] if anomaly_col[k] is not None else -1
                    f.write(f"{i:4d}  {j:4d}  {d1:12.6f}  {d2:12.6f}  {an:12.6f}  {ac:4d}\n")
        print(f"Saved data: {args.save_data}")

    # --- Flagging ---
    missing = {k for k, v in means.items() if v is None}
    flagged = set(missing)
    if args.threshold is not None:
        flagged |= {k for k in means if means[k] is not None
                    and (dev1[k] > args.threshold or dev2[k] > args.threshold)}
    if args.anomaly_threshold is not None:
        flagged |= {k for k in means if means[k] is not None
                    and anomaly[k] > args.anomaly_threshold}

    if flagged and (args.threshold is not None or args.anomaly_threshold is not None):
        entries = write_failed_windows(flagged, rows, cols, args.failed_out)
        print(f"\nFlagged {len(flagged)} windows → {args.failed_out}")
        for i, j, d in entries:
            print(f"  {i} {j} {d}")
    elif args.threshold is None and args.anomaly_threshold is None:
        print("(no --threshold or --anomaly-threshold set, skipping failed_windows.dat)")

    # --- Plot ---
    X, Y = np.meshgrid(cols, rows)  # x=free coord (j), y=fixed coord (i)

    panels = [
        (mat1,        f"|mean - target|  col{args.rst_cols[0]}",  "Reds",    args.threshold),
        (mat2,        f"|mean - target|  col{args.rst_cols[1]}",  "Reds",    args.threshold),
        (mat_anomaly, "Non-restrained anomaly (mean z-score)",      "Oranges", args.anomaly_threshold),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (mat, title, cmap_name, thr) in zip(axes, panels):
        valid = mat[~np.isnan(mat)]
        if thr is not None and len(valid) > 0 and valid.max() > thr > 0:
            norm = TwoSlopeNorm(vmin=0, vcenter=thr, vmax=valid.max())
            below = plt.get_cmap("Greens_r")(np.linspace(0.25, 0.85, 128))
            above = plt.get_cmap("Reds")(np.linspace(0.35, 0.95, 128))
            cmap = LinearSegmentedColormap.from_list("thr_split", np.vstack([below, above]))
        else:
            norm = None
            cmap = plt.get_cmap(cmap_name).copy()
        cmap.set_bad(color="lightgray")
        im = ax.pcolormesh(X, Y, mat, cmap=cmap, norm=norm, shading="auto")
        plt.colorbar(im, ax=ax)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Free coord window (j)")
        ax.set_ylabel("Fixed coord window (i)")

    fig.tight_layout()
    if args.save:
        fig.savefig(args.save, dpi=150)
        print(f"Saved: {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
