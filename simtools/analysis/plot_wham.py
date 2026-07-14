#!/usr/bin/env python3
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt

COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
          "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan"]


def load_wham_data(filename):
    data = []
    with open(filename) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            data.append([float(x) for x in line.split()])
    return np.array(data)


def find_nearest_idx(array, value):
    return (np.abs(array - value)).argmin()


def load_hist_data(histfile, col=2, last=None):
    data = []
    with open(histfile) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data.append(float(line.split()[col - 1]))
            except (ValueError, IndexError):
                continue
    data = np.array(data)
    return data[-last:] if last is not None else data


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Plot one or more WHAM free energy profiles. "
            "Pass one folder for a single curve, multiple folders to compare. "
            "All curves are aligned to the first one when --align-at is given."
        )
    )
    parser.add_argument("folders",      nargs="+",      help="Folders containing the WHAM output file")
    parser.add_argument("--file",       default="wham.out")
    parser.add_argument("--out",        default="wham_plot.png")
    parser.add_argument("--title",      default="Free energy profile")
    parser.add_argument("--xlabel",     default="Reaction coordinate (Å)")
    parser.add_argument("--ylabel",     default="Free energy (kcal/mol)")
    parser.add_argument("--align-at",   type=float, default=None, dest="align_at",
                        help="x value at which all curves are aligned to curve 1")
    parser.add_argument("--labels",     type=str, nargs="+", default=None,
                        help="Legend labels, one per folder (default: folder name)")
    parser.add_argument("--offsets",    type=float, nargs="*", default=None,
                        help="Additional manual offset per curve (kcal/mol), one per folder")
    parser.add_argument("--histfile",   default=None, help="File with sampled reaction coordinate")
    parser.add_argument("--histcol",    type=int, default=2)
    parser.add_argument("--histbins",   type=int, default=40)
    parser.add_argument("--last",        type=int, default=None,
                        help="Use only the last N rows of each file (default: all)")
    parser.add_argument("--no-arrows",  action="store_false", dest="arrows",
                        help="Hide scan-direction arrows on the first two curves")
    parser.add_argument("--no-legend",  action="store_false", dest="legend",
                        help="Hide the legend")
    parser.add_argument("--fontsize",   type=int, default=14,
                        help="Base font size; labels and title scale from this (default: 14)")
    parser.add_argument("--dpi",        type=int, default=300,
                        help="Resolution when saving (default: 300)")
    args = parser.parse_args()

    fs   = args.fontsize
    fs_l = int(round(fs * 1.15))   # axis labels
    fs_t = int(round(fs * 1.30))   # title
    fs_c = int(round(fs * 0.90))   # tick labels / legend

    n = len(args.folders)
    manual_offsets = list(args.offsets) if args.offsets else [0.0] * n
    manual_offsets += [0.0] * (n - len(manual_offsets))

    datasets = []
    for folder in args.folders:
        d = load_wham_data(os.path.join(folder, args.file))
        if args.last is not None:
            d = d[-args.last:]
        datasets.append((d[:, 0], d[:, 1]))

    x0, F0 = datasets[0]
    auto_offsets = [0.0]
    for xi, Fi in datasets[1:]:
        auto = 0.0
        if args.align_at is not None:
            auto = F0[find_nearest_idx(x0, args.align_at)] - Fi[find_nearest_idx(xi, args.align_at)]
        auto_offsets.append(auto)

    if args.align_at is not None:
        for i in range(1, n):
            total = auto_offsets[i] + manual_offsets[i]
            print(f"  Curve {i+1}: auto={auto_offsets[i]:.3f}  manual={manual_offsets[i]:.3f}  total={total:.3f} kcal/mol")

    fig, ax = plt.subplots(figsize=(8, 5))

    for i, ((xi, Fi), folder) in enumerate(zip(datasets, args.folders)):
        total = auto_offsets[i] + manual_offsets[i]
        color = COLORS[i % len(COLORS)]
        base  = args.labels[i] if args.labels and i < len(args.labels) else folder
        label = base if total == 0 else f"{base} (offset={total:.2f})"
        ax.plot(xi, Fi + total, label=label, color=color, lw=2)

        # Scan-direction arrows for the first two curves only
        if args.arrows and i == 0:
            ymin = (Fi + total).min()
            ax.annotate("", xy=(xi.min() + 0.4, ymin), xytext=(xi.min() + 0.1, ymin),
                        arrowprops=dict(arrowstyle="->", color=color, lw=2))
            ax.text(xi.min() + 0.45, ymin, "1", color=color, fontsize=fs, va="center")
        elif args.arrows and i == 1:
            ymin = (Fi + total).min()
            ax.annotate("", xy=(xi.max() - 0.4, ymin), xytext=(xi.max() - 0.1, ymin),
                        arrowprops=dict(arrowstyle="->", color=color, lw=2))
            ax.text(xi.max() - 0.45, ymin, "2", color=color, fontsize=fs, va="center")

    if args.histfile:
        values = load_hist_data(args.histfile, args.histcol, args.last)
        ax2 = ax.twinx()
        ax2.hist(values, bins=args.histbins, color="gray", alpha=0.3, density=True)
        ax2.set_ylabel("Probability density", color="gray", fontsize=fs_l)
        ax2.tick_params(axis="y", labelcolor="gray", width=1.5, length=5, labelsize=fs_c)
        for spine in ax2.spines.values():
            spine.set_linewidth(1.5)

    ax.set_xlabel(args.xlabel, fontsize=fs_l)
    ax.set_ylabel(args.ylabel, fontsize=fs_l)
    ax.set_title(args.title, fontsize=fs_t, pad=10)
    ax.tick_params(axis='both', which='both',
                   top=True, right=True,
                   labeltop=False, labelright=False,
                   width=1.5, length=5, labelsize=fs_c)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    ax.grid(True, alpha=0.5)
    if args.legend:
        ax.legend(loc="upper left", fontsize=fs_c)
    fig.tight_layout(pad=1.5)
    plt.savefig(args.out, dpi=args.dpi)
    print(f"Saved: {args.out}")
    plt.show()


if __name__ == "__main__":
    main()
