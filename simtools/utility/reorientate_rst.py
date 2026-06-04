#!/usr/bin/env python3
import argparse
import shutil
import os
import numpy as np
import mdtraj as md
from mdtools.core import orient


def reorientate(traj, N_tubes, N_res, step=0):
    CAs       = traj.top.select("name CA")
    n         = len(CAs) // N_tubes
    CAs_tubes = [CAs[i*n:(i+1)*n] for i in range(N_tubes)]
    CAs_top   = np.concatenate([t[:N_res] for t in CAs_tubes])

    frame = traj.xyz[step]
    p0 = frame[CAs].mean(axis=0)
    pZ = frame[CAs_top].mean(axis=0)
    pX = frame[CAs_tubes[0]].mean(axis=0)

    oriented_xyz = np.array([orient(frame[a], p0, pZ, pX) for a in CAs])
    oriented     = md.Trajectory(oriented_xyz[np.newaxis], traj.top.subset(CAs))
    traj.superpose(oriented, 0, atom_indices=CAs,
                   ref_atom_indices=np.arange(len(CAs)))
    return traj


def main():
    parser = argparse.ArgumentParser(
        description="Reorient an AMBER rst7 or pdb structure along the nanotube axis."
    )
    parser.add_argument("format",    choices=["rst", "pdb"])
    parser.add_argument("folder",    help="Directory containing input files")
    parser.add_argument("traj_name", help="Base filename without extension")
    parser.add_argument("suffix",    nargs="?", default="",
                        help="Optional suffix between traj_name and extension")
    parser.add_argument("--N_tubes", type=int, default=9)
    parser.add_argument("--N_res",   type=int, default=8)
    args = parser.parse_args()

    folder = args.folder.rstrip("/") + "/"
    suffix = ("_" + args.suffix) if args.suffix else ""
    base   = f"{folder}{args.traj_name}"

    if args.format == "rst":
        shutil.copy(f"{base}.top",        f"{base}.parm7")
        shutil.copy(f"{base}{suffix}.rst", f"{base}{suffix}.rst7")
        traj = md.load(f"{base}{suffix}.rst7", top=f"{base}.parm7")
    else:
        traj = md.load(f"{base}{suffix}.pdb")

    traj = reorientate(traj, args.N_tubes, args.N_res)

    out_ext = "rst" if args.format == "rst" else "pdb"
    outfile = f"{base}{suffix}_oriented.{out_ext}"

    if args.format == "rst":
        traj.save_amberrst7(outfile)
        os.remove(f"{base}.parm7")
        os.remove(f"{base}{suffix}.rst7")
    else:
        traj.save_pdb(outfile)

    print(f"Saved: {outfile}")


if __name__ == "__main__":
    main()
