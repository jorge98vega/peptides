#!/usr/bin/env python3
"""
plot_coords.py — Compare column distributions across specific dump files.

Col 1 is always the simulation step counter.

Layouts:
  coords (default) — one subplot per column, one colour per file.
                     Good for comparing how the same coordinate differs
                     between windows / simulation states.
  files            — one subplot per file, one colour per column.
                     Good for seeing all coordinates of one state at once.

Example:
    plot_coords.py minA.dump minB.dump ts.dump free.dump \\
        --labels 'Min A' 'Min B' 'TS' 'Free' \\
        --cols 2 3 4 5 \\
        --col-labels d1 d2 d3 d4 \\
        --layout coords
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt

COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+",
                        help="Dump files to compare")
    parser.add_argument("--cols", type=int, nargs="+", required=True,
                        help="Columns to plot (1-indexed). Col 1 is the step counter.")
    parser.add_argument("--labels", nargs="+", default=None,
                        help="Label per file (default: filename)")
    parser.add_argument("--col-labels", nargs="+", default=None,
                        help="Label per column (default: 'col N')")
    parser.add_argument("--bins", type=int, default=80,
                        help="Number of histogram bins per column (default: 80)")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="Bar transparency (default: 0.5)")
    parser.add_argument("--last", type=int, default=None,
                        help="Use only the last N rows of each file (default: all)")
    parser.add_argument("--density", action="store_true",
                        help="Normalise histograms to probability density")
    parser.add_argument("--layout", choices=["coords", "files"], default="coords",
                        help="coords (default): one subplot per column, colours=files. "
                             "files: one subplot per file, colours=columns.")
    args = parser.parse_args()

    if 1 in args.cols:
        print("Warning: col 1 is the simulation step counter, not a coordinate.")

    # File labels
    file_labels = list(args.labels) if args.labels else []
    for i in range(len(file_labels), len(args.files)):
        file_labels.append(args.files[i].split('/')[-1])

    # Column labels
    col_labels = list(args.col_labels) if args.col_labels else []
    for i in range(len(col_labels), len(args.cols)):
        col_labels.append(f"col {args.cols[i]}")

    # Load data and extract columns
    # data_by_file[i_file][i_col] = 1D array
    data_by_file = []
    for f in args.files:
        raw = np.loadtxt(f, comments='#')
        if args.last is not None:
            raw = raw[-args.last:]
        data_by_file.append([raw[:, c - 1] for c in args.cols])

    # Bins per column from combined range across all files — keeps bin width
    # consistent between layouts and avoids auto-ranging per individual call
    bins_per_col = []
    for i_c in range(len(args.cols)):
        all_vals = np.concatenate([data_by_file[i_f][i_c]
                                   for i_f in range(len(args.files))])
        bins_per_col.append(np.linspace(all_vals.min(), all_vals.max(),
                                        args.bins + 1))

    if args.layout == "coords":
        n = len(args.cols)
        fig, axes = plt.subplots(1, n, figsize=(max(5, 4 * n), 4), squeeze=False)
        for i_c, (ax, clabel) in enumerate(zip(axes[0], col_labels)):
            bins = bins_per_col[i_c]
            for i_f, flabel in enumerate(file_labels):
                vals  = data_by_file[i_f][i_c]
                color = COLORS[i_f % len(COLORS)]
                ax.hist(vals, bins=bins, alpha=args.alpha, color=color,
                        label=flabel, density=args.density)
                ax.axvline(np.mean(vals), color=color, lw=1.5, ls='--')
            ax.set_xlabel(clabel)
            ax.set_ylabel("Density" if args.density else "Count")
            ax.set_title(clabel)
            ax.legend(fontsize=8)

    else:  # files
        n = len(args.files)
        fig, axes = plt.subplots(1, n, figsize=(max(5, 4 * n), 4), squeeze=False)
        for i_f, (ax, flabel) in enumerate(zip(axes[0], file_labels)):
            for i_c, clabel in enumerate(col_labels):
                vals  = data_by_file[i_f][i_c]
                color = COLORS[i_c % len(COLORS)]
                ax.hist(vals, bins=bins_per_col[i_c], alpha=args.alpha, color=color,
                        label=clabel, density=args.density)
                ax.axvline(np.mean(vals), color=color, lw=1.5, ls='--')
            ax.set_xlabel("Value")
            ax.set_ylabel("Density" if args.density else "Count")
            ax.set_title(flabel)
            ax.legend(fontsize=8)

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
