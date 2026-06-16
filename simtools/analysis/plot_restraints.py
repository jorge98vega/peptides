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
    return np.vstack(blocks), lengths, files


def plot_single(path, select=None, nmax=None, last=None, out="restraints_plot.png"):
    data  = np.loadtxt(path)
    steps = data[:, 0]
    rsts  = data[:, 1:]
    n_steps, n_rsts = rsts.shape
    n_plot = min(nmax, n_rsts) if nmax is not None else n_rsts

    if select is not None and not (1 <= select <= n_plot):
        raise ValueError(f"--select {select} out of range (1–{n_plot})")

    fig, ax = plt.subplots(figsize=(10, 6))
    alpha_bg = 0.25 if select is not None else 1.0
    lines = []
    for idx in range(n_plot):
        is_sel = (select is not None and idx == select - 1)
        ln, = ax.plot(steps, rsts[:, idx],
                      alpha=1.0 if is_sel else alpha_bg,
                      lw=2.0 if is_sel else 1.0,
                      label=f"Restraint {idx+1}")
        lines.append(ln)

    if select is not None:
        color  = lines[select - 1].get_color()
        r_data = rsts[:, select - 1]
        if last is not None:
            start    = n_steps - last
            mean_val = r_data[start:].mean()
            ax.axvline(steps[start], color="gray", lw=1, ls="--")
            ax.hlines(mean_val, steps[start], steps[-1],
                      colors=color, linestyles="--", lw=2)
        else:
            mean_val = r_data.mean()
            ax.axhline(mean_val, color=color, linestyle="--", lw=2)
        ax.text(steps[-1], mean_val, f"  {mean_val:.2f}",
                va="bottom", ha="left", fontsize=10, color=color,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
        print(f"Restraint {select} mean: {mean_val:.4f}")

    ax.set_xlabel("Simulation step")
    ax.set_ylabel("Restraint value")
    ax.set_title("Restraints over time")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    print(f"Saved: {out}")
    plt.show()


def plot_umbrella(directory, ymin=None, ymax=None, first_center=None, step_center=None,
                  nmax=10, prefix="wham", suffix="_rst_1.dump", out="umbrella_restraints_plot.png"):
    data, lengths, files = load_dump_files(directory, prefix, suffix)
    steps = np.arange(len(data))
    rsts  = data[:, 1:]

    fig, ax = plt.subplots(figsize=(12, 6))
    for idx in range(min(nmax, rsts.shape[1])):
        ax.plot(steps, rsts[:, idx], label=f"Restraint {idx+1}", alpha=0.8)

    start_idx = 0
    for i, (split, fname) in enumerate(zip(np.cumsum(lengths), files)):
        ax.axvline(split, color="gray", lw=1)
        mid = (start_idx + split) / 2
        label = fname[len(prefix):len(fname)-len(suffix)].strip("_")
        ax.text(mid, 1.0, label, transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=7, rotation=90, color="dimgray")
        if first_center is not None and step_center is not None:
            center = first_center + i * step_center
            ax.hlines(center, start_idx, split, colors="black", linestyles="--", lw=1)
        start_idx = split

    ax.set_xlabel("Concatenated step")
    ax.set_ylabel("Restraint value")
    ax.set_title("Umbrella sampling restraints across windows")
    ax.legend()
    ax.grid(True, axis="y")
    if ymin is not None or ymax is not None:
        ax.set_ylim(bottom=ymin, top=ymax)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
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
    parser.add_argument("--out",          default=None)
    parser.add_argument("--select",       type=int,   default=None,
                        help="Highlight restraint N (1-indexed) and show its mean (single mode only)")
    parser.add_argument("--last",         type=int,   default=None,
                        help="Compute mean over last N steps only (single mode)")
    parser.add_argument("--nmax",         type=int,   default=None,
                        help="Max number of restraints to plot (default: all in single, 10 in umbrella)")
    parser.add_argument("--ymin",         type=float, default=None)
    parser.add_argument("--ymax",         type=float, default=None)
    parser.add_argument("--first-center", type=float, default=None, dest="first_center",
                        help="First window center (draws dashed center lines, umbrella mode)")
    parser.add_argument("--step-center",  type=float, default=None, dest="step_center",
                        help="Step between window centers (umbrella mode)")
    parser.add_argument("--prefix",       default="wham",        help="Dump file name prefix")
    parser.add_argument("--suffix",       default="_rst_1.dump", help="Dump file name suffix")
    args = parser.parse_args()

    if os.path.isfile(args.path):
        plot_single(args.path, args.select, args.nmax, args.last,
                    out=args.out or "restraints_plot.png")
    elif os.path.isdir(args.path):
        if args.select is not None:
            print("Warning: --select is ignored in umbrella mode (pass a single dump file to use it).")
        plot_umbrella(args.path, args.ymin, args.ymax,
                      args.first_center, args.step_center,
                      args.nmax or 10, args.prefix, args.suffix,
                      out=args.out or "umbrella_restraints_plot.png")
    else:
        raise FileNotFoundError(f"'{args.path}' is not a file or directory")


if __name__ == "__main__":
    main()
