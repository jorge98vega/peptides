#!/usr/bin/env python3
import argparse
import json
import os.path
import numpy as np
import mdtraj as md
from mdtools.core import orient
from mdtools.analysis import get_particle_indices


def build_ca_selections(traj, cfg):
    N_tubes          = cfg["N_tubes"]
    N_rings          = cfg["N_rings"]
    N_res            = cfg["N_res"]
    channel_residues = cfg["channel_residues"]   # N_tubes lists of N_rings 1-indexed resids
    channel_resnames = cfg.get("channel_resnames", ["LYS", "LYN"])

    CAs       = traj.top.select("name CA")
    n         = len(CAs) // N_tubes
    CAs_tubes = [CAs[i*n:(i+1)*n] for i in range(N_tubes)]
    CAs_top   = np.concatenate([t[:N_res]  for t in CAs_tubes])
    CAs_bot   = np.concatenate([t[-N_res:] for t in CAs_tubes])

    resnames_str = " ".join(channel_resnames)
    tube_canal = []
    for ch_res in channel_residues:
        resids_str = " ".join(str(r - 1) for r in ch_res)  # mdtraj uses 0-indexed resid
        sel = traj.top.select(
            f"resid {resids_str} and resname {resnames_str} and name CA"
        )
        tube_canal.append(sel)

    # Interleave by ring: ring0-tube0, ring0-tube1, ..., ring1-tube0, ...
    CAs_canal = np.array([tube_canal[t][i]
                           for i in range(N_rings)
                           for t in range(N_tubes)])

    return {
        "all":    CAs,
        "tubes":  CAs_tubes,
        "top":    CAs_top,
        "bot":    CAs_bot,
        "canal":  CAs_canal,
    }


def reorientate(traj, CAs):
    step  = len(traj) - 1
    frame = traj.xyz[step]
    p0 = frame[CAs["all"]].mean(axis=0)
    pZ = frame[CAs["top"]].mean(axis=0)
    pX = frame[CAs["tubes"][0]].mean(axis=0)

    oriented_xyz = np.array([orient(frame[a], p0, pZ, pX) for a in CAs["all"]])
    oriented     = md.Trajectory(oriented_xyz[np.newaxis], traj.top.subset(CAs["all"]))
    traj.superpose(oriented, 0, atom_indices=CAs["all"],
                   ref_atom_indices=np.arange(len(CAs["all"])))
    return traj


def save_indices(traj, indices, savefile):
    np.save(f"{savefile}.npy", indices)
    with open(f"{savefile}.dat", "w") as f:
        for frame_atoms in indices:
            f.write(" ".join(str(a) for a in frame_atoms) + "\n")
    with open(f"{savefile}_res.dat", "w") as f:
        for frame_atoms in indices:
            resids = [traj.top.atom(a).residue.index + 1 for a in frame_atoms]
            f.write(" ".join(str(r) for r in resids) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Find water indices inside nanotube channels along a trajectory."
    )
    parser.add_argument("--config",    required=True, help="JSON system config")
    parser.add_argument("top",         help="Topology file (.parm7 or .pdb)")
    parser.add_argument("input_traj",  help="Input trajectory (pre-RMSD fit)")
    parser.add_argument("output_traj", help="RMSD-fitted trajectory (created if absent)")
    parser.add_argument("--first", type=int, default=None)
    parser.add_argument("--last",  type=int, default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    N_res   = cfg["N_res"]
    N_tubes = cfg["N_tubes"]
    kw      = dict(first=args.first, last=args.last)

    if not os.path.isfile(args.output_traj):
        print("Reorienting trajectory...")
        traj = md.load(args.input_traj, top=args.top)
        CAs  = build_ca_selections(traj, cfg)
        traj = reorientate(traj, CAs)
        traj.save(args.output_traj)
    else:
        traj = md.load(args.output_traj, top=args.top)
        CAs  = build_ca_selections(traj, cfg)

    WATs = traj.top.select("resname WAT and name O")

    print("Analysing bundle...")
    iWATs = get_particle_indices(traj, WATs, CAs["top"], CAs["bot"],
                                 delta=0.5, **kw)
    save_indices(traj, iWATs, "iWATs")

    print("Analysing canal...")
    iWATs_canal = get_particle_indices(traj, iWATs,
                                       CAs["canal"][:N_tubes],
                                       CAs["canal"][-N_tubes:],
                                       delta=-0.1, preselected=True, **kw)
    save_indices(traj, iWATs_canal, "iWATs_canal")

    print("Analysing tube 1...")
    tube1 = CAs["tubes"][0]
    iWATs_tube1 = get_particle_indices(traj, iWATs,
                                       tube1[:N_res], tube1[-N_res:],
                                       delta=0.0, preselected=True, **kw)
    save_indices(traj, iWATs_tube1, "iWATs_tube1")


if __name__ == "__main__":
    main()
