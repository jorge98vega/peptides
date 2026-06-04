#!/usr/bin/env python3
import json
import argparse
import numpy as np
import re


def rotate_z(pos, center, alpha_deg):
    alpha = np.radians(alpha_deg)
    R = np.array([
        [np.cos(alpha), -np.sin(alpha), 0],
        [np.sin(alpha),  np.cos(alpha), 0],
        [0,              0,             1]
    ])
    return R @ (pos - center) + center


def read_pdb(pdbfile, Ntotal):
    regex = re.compile(
        r"(?:ATOM|HETATM)\s+\d+\s+(\S+)\s+(\S+)\s+\S?\s*(\d+)\s+"
        r"(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)"
    )
    names, resnames, resids, positions = [], [], [], []
    resid = 0
    prev_resid = ""

    with open(pdbfile) as f:
        for line in f:
            if len(names) >= Ntotal:
                break
            m = regex.match(line)
            if m:
                atom_name, res_name, cur_resid, x, y, z = m.groups()
                if cur_resid != prev_resid:
                    prev_resid = cur_resid
                    resid += 1
                names.append(atom_name)
                resnames.append(res_name)
                resids.append(resid)
                positions.append([float(x), float(y), float(z)])

    return names, resnames, np.array(resids), np.array(positions)


def write_clone(f, names, resnames, resids, positions, Natoms, Nrings, atom_offset, resid_offset):
    for ring in range(Nrings):
        for atom in range(Natoms):
            idx  = ring * Natoms + atom
            atid = atom_offset + idx + 1
            rid  = resid_offset + resids[idx]
            pos  = positions[idx]
            f.write(f"ATOM  {atid:5d}  {names[idx]:<4} {resnames[idx]:<3} {rid:4d}    ")
            f.write(f"{pos[0]:8.3f}{pos[1]:8.3f}{pos[2]:8.3f}  0.00  0.00\n")
        f.write("TER   \n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Clean and/or clone a nanotube PDB structure from a JSON config. "
            "Without 'clones' in the config, writes a single renumbered copy. "
            "With 'clones', applies per-clone translation and Z-axis rotation."
        )
    )
    parser.add_argument("--config", required=True, help="JSON config file")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    pdbfile = cfg["pdbfile"]
    newfile = cfg["newfile"]
    Nrings  = cfg["Nrings"]
    Nres    = cfg["Nres"]
    Natoms  = cfg["Natoms"]
    Ntotal  = Nrings * Natoms
    clones  = cfg.get("clones", [{"translation": [0.0, 0.0, 0.0], "angle": 0.0}])

    names, resnames, resids, positions = read_pdb(pdbfile, Ntotal)
    if len(names) < Ntotal:
        raise ValueError(f"Expected {Ntotal} atoms, found {len(names)} in {pdbfile}")

    com = positions.mean(axis=0)

    with open(newfile, "w") as f:
        f.write("\n")
        for n, clone in enumerate(clones):
            t     = np.array(clone.get("translation", [0.0, 0.0, 0.0]))
            angle = clone.get("angle", 0.0)
            new_pos = np.array([rotate_z(p, com, angle) + t for p in positions])
            write_clone(f, names, resnames, resids, new_pos,
                        Natoms, Nrings,
                        atom_offset=n * Ntotal,
                        resid_offset=n * Nrings * Nres)
        f.write("END   \n")

    mode = "clone" if len(clones) > 1 or clones[0].get("translation", [0,0,0]) != [0,0,0] else "clean"
    print(f"{mode}: {len(clones)} copy/copies → {newfile}")


if __name__ == "__main__":
    main()
