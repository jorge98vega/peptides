#!/usr/bin/env python3
"""
plot_dos_cp2k.py — Plot DOS from CP2K projected DOS files.

Reads dos_*.dat files pre-processed from CP2K .pdos output (via pdos2dat.sh).
Each file has a header line with orbital labels (e s p [d]) followed by data rows.
Energy is expected to be already in eV and Fermi-shifted (HOMO at 0).

Usage:
    plot_dos_cp2k.py [--folder .] [--total dos_all.dat]
                     [--files dos_backbone.dat:Backbone dos_phe.dat:PHE ...]
                     [--homo 0] [--lumo 3.5]
                     [--title "CP2K DOS"] [--xlim -4 7] [--save out.png]
"""
import os
import re
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt

AU_TO_EV = 27.211


def find_homo_lumo(folder):
    """Auto-detect HOMO/LUMO from the first *.pdos file found in folder.
    Eigenvalues are in a.u.; result is shifted to Fermi=0 in eV."""
    pdos_files = sorted(glob.glob(os.path.join(folder, "*.pdos")))
    if not pdos_files:
        return None, None

    fermi_au = homo_au = lumo_au = None
    with open(pdos_files[0]) as f:
        header = f.readline()
        m = re.search(r'E\(Fermi\)\s*=\s*([-\d.]+)\s*a\.u\.', header)
        if m:
            fermi_au = float(m.group(1))
        f.readline()  # skip column header
        for line in f:
            parts = line.split()
            if len(parts) < 3:
                continue
            energy_au = float(parts[1])
            occ       = float(parts[2])
            if occ > 0.5:
                homo_au = energy_au
            elif homo_au is not None and lumo_au is None:
                lumo_au = energy_au
                break

    if fermi_au is None:
        return None, None
    homo = (homo_au - fermi_au) * AU_TO_EV if homo_au is not None else None
    lumo = (lumo_au - fermi_au) * AU_TO_EV if lumo_au is not None else None
    return homo, lumo


def read_dos(filename):
    with open(filename) as f:
        header = f.readline().split()
    has_d = 'd' in header
    data = np.loadtxt(filename, skiprows=1)
    energy = data[:, 0]
    total = data[:, 1] + data[:, 2]
    if has_d:
        total += data[:, 3]
    return energy, total


def plot_dos(total_file, partial_files, homo, lumo, title, xlim, save):
    plt.figure(figsize=(10, 6))

    energy, dos = read_dos(total_file)
    plt.plot(energy, dos, 'k', lw=2, label="Total")

    for filepath, label in partial_files:
        energy, dos = read_dos(filepath)
        plt.plot(energy, dos, lw=2, label=label)

    plt.xlabel("Energy (eV)")
    plt.ylabel("DOS")
    plt.title(title)
    if homo is not None:
        plt.axvline(homo, c='k',    ls='--', lw=2, label=f"HOMO ({homo:.2f} eV)")
    if lumo is not None:
        plt.axvline(lumo, c='gray', ls='--', lw=2, label=f"LUMO ({lumo:.2f} eV)")
    plt.xlim(xlim)
    plt.xticks(np.arange(int(xlim[0]), int(xlim[1]) + 1))
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if save:
        plt.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot CP2K DOS from dos_*.dat files")
    parser.add_argument("--folder", default=".",           help="Folder with dos_*.dat files (default: .)")
    parser.add_argument("--total",  default="dos_all.dat", help="Total DOS file (default: dos_all.dat)")
    parser.add_argument("--files",  nargs="+", default=None, metavar="FILE:LABEL",
                        help="Partial DOS files with labels, e.g. dos_backbone.dat:Backbone dos_phe.dat:PHE. "
                             "If omitted, looks for dos_backbone/phe/lys/water*.dat automatically.")
    parser.add_argument("--homo",   type=float, default=None, help="HOMO energy in eV; auto-detected from *.pdos if omitted")
    parser.add_argument("--lumo",   type=float, default=None, help="LUMO energy in eV; auto-detected from *.pdos if omitted")
    parser.add_argument("--title",  default="CP2K DOS",       help="Plot title")
    parser.add_argument("--xlim",   type=float, nargs=2, default=[-4, 7], metavar=("XMIN", "XMAX"))
    parser.add_argument("--save",   default=None,             help="Output image path")
    args = parser.parse_args()

    homo, lumo = args.homo, args.lumo
    if homo is None or lumo is None:
        h, l = find_homo_lumo(args.folder)
        if homo is None:
            homo = h
        if lumo is None:
            lumo = l
        if homo is not None:
            print(f"Auto-detected HOMO: {homo:.5f} eV")
        if lumo is not None:
            print(f"Auto-detected LUMO: {lumo:.5f} eV")

    total_file = os.path.join(args.folder, args.total)

    if args.files:
        partial_files = []
        for item in args.files:
            fname, label = item.rsplit(":", 1)
            partial_files.append((os.path.join(args.folder, fname), label))
    else:
        # Auto-detect named partial DOS files (legacy convention)
        named = [
            ("dos_backbone.dat",     "Backbone"),
            ("dos_phe.dat",          "PHE"),
            ("dos_lys.dat",          "LYS"),
            ("dos_water.dat",        "Water"),
            ("dos_waterchannel.dat", "Water channel"),
            ("dos_waterlumen.dat",   "Water lumen"),
        ]
        partial_files = [(os.path.join(args.folder, f), l) for f, l in named
                         if os.path.isfile(os.path.join(args.folder, f))]

        # Fall back to dos_listN.dat convention (cp2k_pdos2dat.sh output),
        # skipping list1 which is the total (dos_all.dat)
        if not partial_files:
            n = 2
            while True:
                f = os.path.join(args.folder, f"dos_list{n}.dat")
                if not os.path.isfile(f):
                    break
                partial_files.append((f, f"list{n}"))
                n += 1

    plot_dos(total_file, partial_files, homo, lumo,
             args.title, args.xlim, args.save)


if __name__ == "__main__":
    main()
