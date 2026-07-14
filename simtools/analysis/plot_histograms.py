#!/usr/bin/env python3
import os
import re
import argparse
import numpy as np
import matplotlib.pyplot as plt


def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def main():
    parser = argparse.ArgumentParser(
        description="Plot coordinate histograms across umbrella sampling windows."
    )
    parser.add_argument("directory",  help="Directory containing dump files")
    parser.add_argument("--col",      type=int,   nargs="+", default=[2],
                        help="Column(s) to histogram (1-indexed, default 2). "
                             "Multiple columns get one subplot each. "
                             "Col 1 is always the simulation step counter.")
    parser.add_argument("--bin-step", type=float, default=0.01, dest="bin_step")
    parser.add_argument("--bin-min",  type=float, default=None, dest="bin_min",
                        help="Lower bin edge (default: data minimum)")
    parser.add_argument("--bin-max",  type=float, default=None, dest="bin_max",
                        help="Upper bin edge (default: data maximum)")
    parser.add_argument("--prefix",   default="wham")
    parser.add_argument("--suffix",   default="_rst_1.dump")
    parser.add_argument("--alpha",    type=float, default=0.5)
    parser.add_argument("--last",     type=int,   default=None,
                        help="Use only the last N rows of each file (default: all)")
    args = parser.parse_args()

    if 1 in args.col:
        print("Warning: col 1 is the simulation step counter, not a coordinate.")

    files = sorted(
        [f for f in os.listdir(args.directory)
         if f.startswith(args.prefix) and f.endswith(args.suffix)],
        key=natural_sort_key
    )
    if not files:
        raise FileNotFoundError(
            f"No files matching '{args.prefix}*{args.suffix}' found in {args.directory}"
        )

    datasets = []
    labels = []
    for f in files:
        raw = np.loadtxt(os.path.join(args.directory, f))
        datasets.append(raw[-args.last:] if args.last is not None else raw)
        label = re.search(rf'{args.prefix}(\d+){args.suffix}', f)
        labels.append(label.group(1) if label else f)

    cols = args.col
    ncols_plot = len(cols)
    fig, axes = plt.subplots(1, ncols_plot,
                             figsize=(max(6, 5 * ncols_plot), 5),
                             squeeze=False)

    for ax, c in zip(axes[0], cols):
        col_vals = [d[:, c - 1] for d in datasets]
        all_c    = np.concatenate(col_vals)
        bin_min  = args.bin_min if args.bin_min is not None else all_c.min()
        bin_max  = args.bin_max if args.bin_max is not None else all_c.max()
        bins     = np.arange(bin_min, bin_max + args.bin_step, args.bin_step)

        for values, label in zip(col_vals, labels):
            ax.hist(values, bins=bins, alpha=args.alpha, label=f"win {label}")
        ax.hist(all_c, bins=bins, histtype="stepfilled",
                facecolor="none", edgecolor="black", lw=1.2, alpha=0.8,
                label="Total")
        ax.set_xlabel(f"Column {c}")
        ax.set_ylabel("Count")
        ax.set_title(f"Col {c} distribution")

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
