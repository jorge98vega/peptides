#!/usr/bin/env python3
"""
plot_dos_fireball.py — Plot DOS from Fireball dens_XXX.dat output.

Supports c(KF)4 monomer/dimer (alternating LYS-PHE blocks). Water atoms are
detected automatically from the bas file if extra atoms are present beyond the
peptide blocks (expects groups of 24 atoms = 8 water molecules).

Usage:
    plot_dos_fireball.py --bas answer_0.bas [--folder .] [--tot dens_TOT.dat]
                         [--homo -5.02] [--lumo -1.04]
                         [--title "Fireball DOS"] [--xlim -9 2] [--save out.png]
"""
import os
import re
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt

LYS_atoms = [
    "N", "H", "CA", "HA", "CB", "HB2", "HB3",
    "CG", "HG2", "HG3", "CD", "HD2", "HD3",
    "CE", "HE2", "HE3", "NZ", "HZ2", "HZ3",
    "C", "O",
]
PHE_atoms = [
    "N", "H", "CA", "HA", "CB", "HB2", "HB3",
    "CG", "CD1", "HD1", "CE1", "HE1", "CZ", "HZ",
    "CE2", "HE2", "CD2", "HD2", "C", "O",
]
BLOCK_SIZE       = 41   # LYS_SIZE (21) + PHE_SIZE (20)
LYS_SIZE         = 21
WATER_GROUP_SIZE = 24   # 8 water molecules × 3 atoms


def find_homo_lumo(folder):
    """Auto-detect HOMO/LUMO from out.txt (Fermi level) and eigen.dat."""
    fermi = None
    out_file = os.path.join(folder, "out.txt")
    if os.path.isfile(out_file):
        with open(out_file) as f:
            for line in f:
                m = re.search(r'Fermi Level\s*=\s*([-\d.]+)', line)
                if m:
                    fermi = float(m.group(1))

    if fermi is None:
        return None, None

    eigen_file = os.path.join(folder, "eigen.dat")
    if not os.path.isfile(eigen_file):
        return fermi, None

    eigenvalues = []
    in_data = False
    with open(eigen_file) as f:
        for line in f:
            if re.search(r'-{4,}', line) or 'eigenvalue' in line.lower():
                in_data = True
                continue
            if in_data:
                eigenvalues.extend(float(x) for x in line.split())

    if not eigenvalues:
        return fermi, None

    homo = max((e for e in eigenvalues if e <= fermi), default=None)
    lumo = min((e for e in eigenvalues if e >  fermi), default=None)
    return homo, lumo


def read_bas(filename):
    with open(filename) as f:
        lines = f.readlines()
    natoms = int(lines[0].strip())
    atoms = [(int(l.split()[0]), *map(float, l.split()[1:4])) for l in lines[1:] if l.strip()]
    return natoms, atoms


def read_tot(filename):
    data = np.loadtxt(filename)
    return data[:, 0], data[:, 1]


def resid_atom_to_index(resid, atom_name, nblocks):
    idx = resid - 1
    block, is_lys = idx // 2, (idx % 2 == 0)
    if block >= nblocks:
        raise ValueError(f"resid {resid} out of range (nblocks={nblocks})")
    offset = block * BLOCK_SIZE
    if is_lys:
        return offset + LYS_atoms.index(atom_name) + 1
    else:
        return offset + LYS_SIZE + PHE_atoms.index(atom_name) + 1


def get_equivalent_atoms(resname, atom_name, nblocks):
    resname = resname.upper()
    atom_list = LYS_atoms if resname == "LYS" else PHE_atoms if resname == "PHE" else None
    if atom_list is None:
        raise ValueError("resname must be 'LYS' or 'PHE'")
    if atom_name not in atom_list:
        raise ValueError(f"{atom_name} not in {resname}")
    resid_fn = (lambda b: 2*b+1) if resname == "LYS" else (lambda b: 2*b+2)
    return [(resid_fn(b), atom_name) for b in range(nblocks)]


def get_water_atoms(atom_type, natoms, atoms, nblocks, group=None):
    peptide_atoms = nblocks * BLOCK_SIZE
    remaining = natoms - peptide_atoms
    if remaining == 0:
        return []
    if remaining % WATER_GROUP_SIZE != 0:
        raise ValueError(f"Extra atoms ({remaining}) not a multiple of {WATER_GROUP_SIZE}")
    n_groups = remaining // WATER_GROUP_SIZE

    if group is not None:
        if not (1 <= group <= n_groups):
            raise ValueError(f"group must be between 1 and {n_groups}")
        start = peptide_atoms + (group - 1) * WATER_GROUP_SIZE
        indices = range(start, start + WATER_GROUP_SIZE)
    else:
        indices = range(peptide_atoms, natoms)

    Z_filter = {"O": 8, "H": 1}
    selection = []
    for i in indices:
        Z = atoms[i][0]
        if atom_type == "all" or Z == Z_filter.get(atom_type):
            selection.append(i + 1)
    return selection


def read_selection_dos(selection, folder, nblocks):
    energy_ref = dos_sum = None
    for item in selection:
        atom_index = item if isinstance(item, int) else resid_atom_to_index(*item, nblocks)
        data = np.loadtxt(os.path.join(folder, f"dens_{atom_index:03d}.dat"))
        energy = data[:, 0]
        dos = 0.5 * np.sum(data[:, 1:-1], axis=1)
        energy_ref = energy if energy_ref is None else energy_ref
        dos_sum = dos if dos_sum is None else dos_sum + dos
    return energy_ref, dos_sum


def plot_dos(energy_tot, dos_tot, curves, homo, lumo, title, xlim, save):
    plt.figure(figsize=(10, 6))
    plt.plot(energy_tot, dos_tot, 'k', lw=2, label="Total")
    for energy, dos, label in curves:
        plt.plot(energy, dos, lw=2, label=label)
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
    parser = argparse.ArgumentParser(description="Plot Fireball DOS for c(KF)4 systems")
    parser.add_argument("--bas",    required=True,              help="Basis file (.bas)")
    parser.add_argument("--folder", default=".",                help="Folder with dens_*.dat files (default: .)")
    parser.add_argument("--tot",    default="dens_TOT.dat",     help="Total DOS file (default: dens_TOT.dat)")
    parser.add_argument("--homo",   type=float, default=None,   help="HOMO energy (eV); auto-detected from out.txt+eigen.dat if omitted")
    parser.add_argument("--lumo",   type=float, default=None,   help="LUMO energy (eV); auto-detected from out.txt+eigen.dat if omitted")
    parser.add_argument("--title",  default="Fireball DOS",     help="Plot title")
    parser.add_argument("--xlim",   type=float, nargs=2, default=[-9, 2], metavar=("XMIN", "XMAX"))
    parser.add_argument("--save",   default=None,               help="Output image path")
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

    natoms, atoms = read_bas(args.bas)
    nblocks = natoms // BLOCK_SIZE

    energy_tot, dos_tot = read_tot(os.path.join(args.folder, args.tot))

    sel_BB = (
        get_equivalent_atoms("LYS", "CA", nblocks) + get_equivalent_atoms("PHE", "CA", nblocks) +
        get_equivalent_atoms("LYS", "N",  nblocks) + get_equivalent_atoms("PHE", "N",  nblocks) +
        get_equivalent_atoms("LYS", "C",  nblocks) + get_equivalent_atoms("PHE", "C",  nblocks) +
        get_equivalent_atoms("LYS", "O",  nblocks) + get_equivalent_atoms("PHE", "O",  nblocks)
    )
    sel_PHE = [a for name in ["CB", "CG", "CD1", "CE1", "CZ", "CE2", "CD2"]
               for a in get_equivalent_atoms("PHE", name, nblocks)]
    sel_LYS = [a for name in ["CB", "CG", "CD", "CE", "NZ"]
               for a in get_equivalent_atoms("LYS", name, nblocks)]

    _, dos_BB  = read_selection_dos(sel_BB,  args.folder, nblocks)
    _, dos_PHE = read_selection_dos(sel_PHE, args.folder, nblocks)
    _, dos_LYS = read_selection_dos(sel_LYS, args.folder, nblocks)

    curves = [
        (energy_tot, dos_BB,  "Backbone"),
        (energy_tot, dos_PHE, "PHE"),
        (energy_tot, dos_LYS, "LYS"),
    ]

    if natoms > nblocks * BLOCK_SIZE:
        sel_w = get_water_atoms("all", natoms, atoms, nblocks)
        _, dos_w = read_selection_dos(sel_w, args.folder, nblocks)
        curves.append((energy_tot, dos_w, "Water"))

    plot_dos(energy_tot, dos_tot, curves,
             homo, lumo, args.title, args.xlim, args.save)


if __name__ == "__main__":
    main()
