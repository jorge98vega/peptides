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
    parser.add_argument("--col",      type=int,   default=1,    help="Column to histogram (1-indexed, default 1)")
    parser.add_argument("--bin-step", type=float, default=0.01, dest="bin_step")
    parser.add_argument("--bin-min",  type=float, default=None, dest="bin_min",
                        help="Lower bin edge (default: data minimum)")
    parser.add_argument("--bin-max",  type=float, default=None, dest="bin_max",
                        help="Upper bin edge (default: data maximum)")
    parser.add_argument("--prefix",   default="wham")
    parser.add_argument("--suffix",   default="_rst_1.dump")
    parser.add_argument("--alpha",    type=float, default=0.5)
    args = parser.parse_args()

    files = sorted(
        [f for f in os.listdir(args.directory)
         if f.startswith(args.prefix) and f.endswith(args.suffix)],
        key=natural_sort_key
    )
    if not files:
        raise FileNotFoundError(
            f"No files matching '{args.prefix}*{args.suffix}' found in {args.directory}"
        )

    all_values = []
    per_window = []
    labels = []
    for f in files:
        data = np.loadtxt(os.path.join(args.directory, f))
        values = data[:, args.col - 1]
        per_window.append(values)
        all_values.append(values)
        label = re.search(rf'{args.prefix}(\d+){args.suffix}', f)
        labels.append(label.group(1) if label else f)

    all_values = np.concatenate(all_values)
    bin_min = args.bin_min if args.bin_min is not None else all_values.min()
    bin_max = args.bin_max if args.bin_max is not None else all_values.max()
    bins = np.arange(bin_min, bin_max + args.bin_step, args.bin_step)

    plt.figure(figsize=(10, 6))
    for values, label in zip(per_window, labels):
        plt.hist(values, bins=bins, alpha=args.alpha, label=f"win {label}")

    plt.hist(all_values, bins=bins, histtype="stepfilled",
             facecolor="none", edgecolor="black", lw=1.2, alpha=0.8, label="Total envelope")

    plt.xlabel(f"Column {args.col}")
    plt.ylabel("Count")
    plt.title(f"Coordinate distributions across windows (col {args.col})")
    #plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
