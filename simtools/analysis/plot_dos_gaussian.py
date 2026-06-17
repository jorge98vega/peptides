#!/usr/bin/env python3
"""
plot_dos_gaussian.py — Plot DOS from Gaussian DOS_curve.txt output.

DOS_curve.txt columns: energy TDOS pdos_0 pdos_1 pdos_2 ...
Default PDOS fragment order (from Multiwfn for c(KF)4):
  0: Backbone   1: Backbone_Hs   2: LYS   3: LYS_Hs   4: PHE   5: PHE_Hs

Usage:
    plot_dos_gaussian.py [--file DOS_curve.txt] [--cols 0 4 2]
                         [--homo -6.55] [--lumo -0.64]
                         [--title "Gaussian DOS"] [--xlim -9 2] [--save out.png]
"""
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt

PDOS_LABELS = ["Backbone", "Backbone_Hs", "LYS", "LYS_Hs", "PHE", "PHE_Hs"]


def find_homo_lumo(dos_file):
    """Auto-detect HOMO/LUMO from orginfo.txt in the same directory as dos_file.
    orginfo.txt columns: energy(eV)  occupation  ..."""
    orginfo = os.path.join(os.path.dirname(os.path.abspath(dos_file)), "orginfo.txt")
    if not os.path.isfile(orginfo):
        return None, None
    homo = lumo = None
    with open(orginfo) as f:
        f.readline()  # header line (n_orbitals, n_columns)
        for line in f:
            parts = line.split()
            if len(parts) < 2:
                continue
            energy = float(parts[0])
            occ    = float(parts[1])
            if occ >= 1.0:
                homo = energy
            elif homo is not None and lumo is None:
                lumo = energy
                break
    return homo, lumo


def read_dos_curve(filename):
    data = np.loadtxt(filename)
    return data[:, 0], data[:, 1], data[:, 2:]


def plot_dos(filename, col_indices, homo, lumo, title, xlim, save):
    energy, tdos, pdos = read_dos_curve(filename)

    plt.figure(figsize=(10, 6))
    plt.plot(energy, tdos, 'k', lw=2, label="Total")

    for i in col_indices:
        label = PDOS_LABELS[i] if i < len(PDOS_LABELS) else f"PDOS col {i}"
        plt.plot(energy, pdos[:, i], lw=2, label=label)

    plt.xlabel("Energy (eV)")
    plt.ylabel("DOS")
    plt.title(title)
    if homo is not None:
        plt.axvline(homo, c='k',    ls='--', lw=2, label=f"HOMO ({homo:.2f} eV)")
    if lumo is not None:
        plt.axvline(lumo, c='gray', ls='--', lw=2, label=f"LUMO ({lumo:.2f} eV)")
    plt.xlim(xlim)
    plt.xticks(range(int(xlim[0]), int(xlim[1]) + 1))
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if save:
        plt.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot Gaussian DOS from DOS_curve.txt")
    parser.add_argument("--file",  default="DOS_curve.txt",  help="Input file (default: DOS_curve.txt)")
    parser.add_argument("--cols",  type=int, nargs="+", default=[0, 4, 2], metavar="COL",
                        help="0-indexed PDOS columns to plot (default: 0 4 2 = Backbone, PHE, LYS)")
    parser.add_argument("--homo",  type=float, default=None, help="HOMO energy (eV); auto-detected from orginfo.txt if omitted")
    parser.add_argument("--lumo",  type=float, default=None, help="LUMO energy (eV); auto-detected from orginfo.txt if omitted")
    parser.add_argument("--title", default="Gaussian DOS",   help="Plot title")
    parser.add_argument("--xlim",  type=float, nargs=2, default=[-9, 2], metavar=("XMIN", "XMAX"))
    parser.add_argument("--save",  default=None,             help="Output image path")
    args = parser.parse_args()

    homo, lumo = args.homo, args.lumo
    if homo is None or lumo is None:
        h, l = find_homo_lumo(args.file)
        if homo is None:
            homo = h
        if lumo is None:
            lumo = l
        if homo is not None:
            print(f"Auto-detected HOMO: {homo:.6f} eV")
        if lumo is not None:
            print(f"Auto-detected LUMO: {lumo:.6f} eV")

    plot_dos(args.file, args.cols, homo, lumo,
             args.title, args.xlim, args.save)


if __name__ == "__main__":
    main()
