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


def read_mask(mask_file, default_jmin, default_jmax):
    """Read mask file (lines: i jmin jmax) → {i: (jmin, jmax)}.
    Rows not listed will use (default_jmin, default_jmax) via in_mask."""
    mask = {}
    with open(mask_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 3:
                mask[int(parts[0])] = (int(parts[1]), int(parts[2]))
    return mask


def in_mask(i, j, mask, default_jmin, default_jmax):
    """Return True if window (i,j) is within the mask for row i."""
    jmin, jmax = mask.get(i, (default_jmin, default_jmax))
    return jmin <= j <= jmax


def write_failed_windows(flagged_or_missing, rows, cols, output_path, valid_set=None):
    """Write one entry per contiguous chain of flagged windows per row.

    A single chain starting at j_min with direction=next is enough:
    run_all_wham2d.sh cascades through the rest automatically.
    Isolated single windows get direction=none.
    valid_set: set of (i,j) within the mask; out-of-mask windows are treated
    as boundaries (not as good neighbors).
    """
    cols_set = set(cols)

    def is_available(i, j):
        if valid_set is not None:
            return (i, j) in valid_set and (i, j) not in flagged_or_missing
        return j in cols_set and (i, j) not in flagged_or_missing

    entries = []
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
                left_good  = is_available(i, chain[0]  - 1)
                right_good = is_available(i, chain[-1] + 1)
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
                        help="1-indexed columns for the two restrained coordinates in the dump file "
                             "(col 1 is the step counter, restraints start at col 2)")
    parser.add_argument("--free-cols",         type=int, nargs="+", metavar="COL",
                        help="1-indexed columns to use as non-restrained (default: all non-restrained); "
                             "(col 1 is the step counter, restraints start at col 2")
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
    parser.add_argument("--mask",              default=None, metavar="FILE",
                        help="Mask file (lines: i jmin jmax) to restrict valid windows per row; "
                             "excluded windows are shown in the heatmap but grayed out")
    args = parser.parse_args()

    if 1 in args.rst_cols:
        print("Warning: col 1 is the simulation step counter, not a coordinate. "
              "Restrained coordinates start at col 2.")
    if args.free_cols and 1 in args.free_cols:
        print("Warning: col 1 is the simulation step counter, not a coordinate. "
              "Restrained coordinates start at col 2.")

    rows = list(range(1, args.rows + 1))
    cols = list(range(1, args.cols + 1))
    c1 = args.rst_cols[0] - 1  # 0-indexed
    c2 = args.rst_cols[1] - 1

    window_mask = read_mask(args.mask, cols[0], cols[-1]) if args.mask else {}
    valid_set = {(i, j) for i in rows for j in cols
                 if in_mask(i, j, window_mask, cols[0], cols[-1])} if window_mask else None

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

    # --- Non-restrained anomaly score (per-row mean z-score across free columns) ---
    # Reference is computed within each row i so the score is insensitive to the
    # natural drift of free coordinates along axis-1. Mean z (not max) aggregates
    # the correlated multi-column signal of bad geometry.
    # Limitation: contaminated when bad windows are a majority within a row.
    anomaly     = {k: (0.0  if v is not None else np.nan) for k, v in means.items()}
    anomaly_col = {k: (None if v is not None else None)   for k, v in means.items()}
    n_free      = {k: 0 for k in means}
    max_z_track = {k: 0.0 for k in means}
    for c in free_col_indices:
        for i in rows:
            row_keys = [(i, j) for j in cols if means.get((i, j)) is not None
                        and (valid_set is None or (i, j) in valid_set)]
            if len(row_keys) < 2:
                continue
            row_vals = np.array([means[k][c] for k in row_keys])
            rmed = np.median(row_vals)
            rstd = row_vals.std()
            if rstd < 1e-10:
                continue
            for k in row_keys:
                z = abs(means[k][c] - rmed) / rstd
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

    # --- Flagging (restricted to valid/masked-in windows) ---
    in_play = valid_set if valid_set is not None else set(means.keys())
    missing = {k for k, v in means.items() if v is None and k in in_play}
    flagged = set(missing)
    if args.threshold is not None:
        flagged |= {k for k in in_play if means.get(k) is not None
                    and (dev1[k] > args.threshold or dev2[k] > args.threshold)}
    if args.anomaly_threshold is not None:
        flagged |= {k for k in in_play if means.get(k) is not None
                    and anomaly[k] > args.anomaly_threshold}

    if flagged and (args.threshold is not None or args.anomaly_threshold is not None):
        entries = write_failed_windows(flagged, rows, cols, args.failed_out,
                                       valid_set=valid_set)
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
        (mat_anomaly, "Non-restrained anomaly (per-row mean z-score)", "Oranges", args.anomaly_threshold),
    ]

    # Precompute mask overlay matrices once (reused for every panel)
    if window_mask:
        excl_mat = np.full((len(rows), len(cols)), np.nan)
        sel_binary = np.zeros((len(rows), len(cols)))
        for ri, i_ in enumerate(rows):
            for ci, j_ in enumerate(cols):
                if in_mask(i_, j_, window_mask, cols[0], cols[-1]):
                    sel_binary[ri, ci] = 1.0
                else:
                    excl_mat[ri, ci] = 1.0
        gray_cmap = LinearSegmentedColormap.from_list("excl_gray", ["#888888", "#888888"])
        gray_cmap.set_bad(alpha=0)

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
        if window_mask:
            ax.pcolormesh(X, Y, excl_mat, cmap=gray_cmap, vmin=0, vmax=1,
                          alpha=0.5, shading="auto")
            ax.contour(np.array(cols), np.array(rows), sel_binary,
                       levels=[0.5], colors="black", linewidths=1.0)
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
