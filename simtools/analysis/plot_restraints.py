#!/usr/bin/env python3
import os
import re
import argparse
import numpy as np
import matplotlib.pyplot as plt


def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def load_dump_files(directory, prefix="wham", suffix="_rst_1.dump"):
    files = sorted(
        [f for f in os.listdir(directory)
         if f.startswith(prefix) and f.endswith(suffix)],
        key=natural_sort_key
    )
    blocks, lengths = [], []
    for f in files:
        try:
            data = np.loadtxt(os.path.join(directory, f))
            blocks.append(data)
            lengths.append(len(data))
        except Exception as e:
            print(f"Warning: could not read {f}: {e}")
    if not blocks:
        raise FileNotFoundError(f"No dump files matching '{prefix}*{suffix}' found in {directory}")
    return np.vstack(blocks), lengths


def plot_single(path, restraint=None, last=None, out="restraints_plot.png"):
    data  = np.loadtxt(path)
    steps = data[:, 0]
    rsts  = data[:, 1:]
    n_steps, n_rsts = rsts.shape

    plt.figure(figsize=(10, 6))
    for idx in range(n_rsts):
        plt.plot(steps, rsts[:, idx], label=f"Restraint {idx+1}")

    if restraint is not None:
        if not (1 <= restraint <= n_rsts):
            raise ValueError(f"--restraint {restraint} out of range (1–{n_rsts})")
        r_data = rsts[:, restraint - 1]
        if last is not None:
            start = n_steps - last
            mean_val = r_data[start:].mean()
            plt.axvline(steps[start], color="gray", lw=1)
            plt.hlines(mean_val, steps[start], steps[-1], colors="black", linestyles="--", lw=1)
        else:
            mean_val = r_data.mean()
            plt.axhline(mean_val, color="black", linestyle="--", lw=1)
        plt.text(steps[-1], mean_val, f"{mean_val:.2f}",
                 va="bottom", ha="right", fontsize=10,
                 bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"))

    plt.xlabel("Simulation step")
    plt.ylabel("Restraint value")
    plt.title("Restraints over time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out, dpi=300)
    print(f"Saved: {out}")
    plt.show()


def plot_umbrella(directory, ymin=None, ymax=None, first_center=None, step_center=None,
                  nmax=10, prefix="wham", suffix="_rst_1.dump", out="umbrella_restraints_plot.png"):
    data, lengths = load_dump_files(directory, prefix, suffix)
    steps = np.arange(len(data))
    rsts  = data[:, 1:]

    plt.figure(figsize=(12, 6))
    for idx in range(min(nmax, rsts.shape[1])):
        plt.plot(steps, rsts[:, idx], label=f"Restraint {idx+1}", alpha=0.8)

    start_idx = 0
    for i, split in enumerate(np.cumsum(lengths)):
        plt.axvline(split, color="gray", lw=1)
        if first_center is not None and step_center is not None:
            center = first_center + i * step_center
            plt.hlines(center, start_idx, split, colors="black", linestyles="--", lw=1)
            start_idx = split

    plt.xlabel("Concatenated step")
    plt.ylabel("Restraint value")
    plt.title("Umbrella sampling restraints across windows")
    plt.legend()
    plt.grid(True, axis="y")
    if ymin is not None or ymax is not None:
        plt.ylim(bottom=ymin, top=ymax)
    plt.tight_layout()
    plt.savefig(out, dpi=300)
    print(f"Saved: {out}")
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Plot restraint data. Pass a dump file for single-window mode, "
            "or a directory of dump files for umbrella sampling mode (auto-detected)."
        )
    )
    parser.add_argument("path",          help="Dump file or directory of dump files")
    parser.add_argument("--out",         default=None)
    # Single-window options
    parser.add_argument("--restraint",   type=int,   default=None,
                        help="Highlight restraint N (1-indexed) and show its mean")
    parser.add_argument("--last",        type=int,   default=None,
                        help="Compute mean over last N steps only")
    # Umbrella options
    parser.add_argument("--ymin",        type=float, default=None)
    parser.add_argument("--ymax",        type=float, default=None)
    parser.add_argument("--first-center",type=float, default=None, dest="first_center",
                        help="First window center (draws dashed center lines)")
    parser.add_argument("--step-center", type=float, default=None, dest="step_center",
                        help="Step between window centers")
    parser.add_argument("--nmax",        type=int,   default=10,
                        help="Max number of restraints to plot (umbrella mode, default 10)")
    parser.add_argument("--prefix",      default="wham",        help="Dump file name prefix")
    parser.add_argument("--suffix",      default="_rst_1.dump", help="Dump file name suffix")
    args = parser.parse_args()

    if os.path.isfile(args.path):
        plot_single(args.path, args.restraint, args.last,
                    out=args.out or "restraints_plot.png")
    elif os.path.isdir(args.path):
        plot_umbrella(args.path, args.ymin, args.ymax,
                      args.first_center, args.step_center,
                      args.nmax, args.prefix, args.suffix,
                      out=args.out or "umbrella_restraints_plot.png")
    else:
        raise FileNotFoundError(f"'{args.path}' is not a file or directory")


if __name__ == "__main__":
    main()
