#!/usr/bin/env python3
"""
plot_hbond_hists.py — H-bond distance and angle distributions.

Reads mdtools hbonds CSV files (columns: index, step, donor, h, acceptor, d[, theta])
and plots distance / angle histograms comparing multiple simulations.

Uses mdtools.core.MyAtom.from_string to parse donor/acceptor atom strings.
Requires the 'peptides' conda environment (pandas + mdtools).

Layout: rows = bond types, columns = distance | angle.
The angle panel is hidden when no simulation provides theta for that bond type.

Run with:
    conda run -n peptides python plot_hbond_hists.py [args]

Example:
    plot_hbond_hists.py \\
        --csv 'MD:channel1_hbonds.csv' \\
              'QM/MM:qmmm/MD_hbonds.csv' \\
        --bonds 'Lys$^+$-water:LYS:HOH' \\
                'Lys$^+$-Lys:LYS:LYN' \\
        --density --bins 60
"""
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, '/home/jorge/research/peptides/simulations/peptides')
from mdtools.core import MyAtom

COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']


def load_qmmask(path):
    """Return set of 0-based atom indices in the QM zone (qmmask uses 1-based serials)."""
    with open(path) as f:
        tokens = f.read().split()
    return set(int(t) - 1 for t in tokens if t.isdigit())


def parse_res_atom(spec):
    """Split 'RES' or 'RES/ATOM' into (resname, atomname_or_None)."""
    if '/' in spec:
        res, atom = spec.split('/', 1)
        return res, atom
    return spec, None


def load_hbonds(path, donor_res, acc_res,
                donor_atom=None, acc_atom=None,
                qm_indices=None, mode='qm'):
    """Return (d, theta_or_None) arrays for bonds matching the given filters.

    donor_res/acc_res  : residue name filter (required).
    donor_atom/acc_atom: atom name filter (optional; None = any atom of that residue).
    qm_indices         : set of 0-based atom indices in the QM zone, or None (no filter).
    mode               : 'qm' — keep bonds where both donor AND acceptor are in QM.
                         'mm' — keep bonds where neither donor NOR acceptor is in QM.
    """
    df = pd.read_csv(path, index_col=0)

    def match(col, resname, atomname):
        atoms = col.apply(MyAtom.from_string)
        m = atoms.apply(lambda a: a.resname) == resname
        if atomname is not None:
            m &= atoms.apply(lambda a: a.name) == atomname
        return m

    df = df[match(df['donor'], donor_res, donor_atom) &
            match(df['acceptor'], acc_res, acc_atom)]

    if qm_indices is not None:
        d_in = df['donor'].apply(lambda s: MyAtom.from_string(s).index in qm_indices)
        a_in = df['acceptor'].apply(lambda s: MyAtom.from_string(s).index in qm_indices)
        df = df[d_in & a_in] if mode == 'qm' else df[~d_in & ~a_in]

    d  = df['d'].values
    th = df['theta'].values if 'theta' in df.columns else None
    return d, th


def style_ax(ax, fs_l, fs_c):
    ax.tick_params(axis='both', which='both',
                   top=True, right=True,
                   labeltop=False, labelright=False,
                   width=1.5, length=5, labelsize=fs_c)
    for sp in ax.spines.values():
        sp.set_linewidth(1.5)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--csv', nargs='+', required=True,
                        help='LABEL:PATH for each simulation CSV')
    parser.add_argument('--bonds', nargs='+', required=True,
                        help='LABEL:DONOR_RESNAME:ACC_RESNAME for each bond type. '
                             'Append /ATOMNAME to restrict by atom, e.g. LYS/NZ:LYN/NZ.')
    parser.add_argument('--qmmask', nargs='+', default=None,
                        help='qmmask.dat file(s), one per --csv entry (or one shared). '
                             'Prefix with "qm:" (default) to keep QM-QM bonds, '
                             'or "mm:" to keep MM-MM bonds (excludes any bond involving '
                             'a QM atom). Use "none" to skip filtering for that entry.')
    parser.add_argument('--bins',    type=int,   default=60,
                        help='Bins per panel (default: 60)')
    parser.add_argument('--alpha',   type=float, default=0.5)
    parser.add_argument('--density', action='store_true',
                        help='Normalise to probability density')
    parser.add_argument('--dmin',    type=float, default=None,
                        help='Minimum distance cutoff in Å (applied before binning)')
    parser.add_argument('--fontsize', type=int, default=14)
    parser.add_argument('--dpi',      type=int, default=300)
    parser.add_argument('--save',     default=None,
                        help='Save figure to this path')
    args = parser.parse_args()

    fs   = args.fontsize
    fs_l = int(round(fs * 1.15))
    fs_t = int(round(fs * 1.30))
    fs_c = int(round(fs * 0.90))

    sims  = [s.split(':', 1) for s in args.csv]    # [[label, path], ...]
    # bonds: [[label, don_spec, acc_spec], ...] where spec is 'RES' or 'RES/ATOM'
    bonds = [b.split(':', 2) for b in args.bonds]

    # Build per-sim (qm_indices, mode) pairs — (None, 'qm') means no filtering
    qm_filters = [(None, 'qm')] * len(sims)
    if args.qmmask:
        masks = args.qmmask
        if len(masks) == 1:
            masks = masks * len(sims)   # broadcast single mask to all sims
        for i, token in enumerate(masks):
            if token.lower() == 'none':
                continue
            if token.startswith('mm:'):
                mode, mpath = 'mm', token[3:]
            elif token.startswith('qm:'):
                mode, mpath = 'qm', token[3:]
            else:
                mode, mpath = 'qm', token
            indices = load_qmmask(mpath)
            qm_filters[i] = (indices, mode)
            print(f'QM mask ({mode}) for {sims[i][0]}: {len(indices)} atoms from {mpath}')

    n_bonds = len(bonds)
    fig, axes = plt.subplots(n_bonds, 2,
                             figsize=(11, 4 * n_bonds),
                             squeeze=False)

    for row, (bond_label, don_spec, acc_spec) in enumerate(bonds):
        don_res, don_atom = parse_res_atom(don_spec)
        acc_res, acc_atom = parse_res_atom(acc_spec)
        ax_d  = axes[row, 0]
        ax_th = axes[row, 1]

        d_all, th_all = [], []
        per_sim = []

        for (sim_label, path), (qm_idx, qm_mode) in zip(sims, qm_filters):
            print(f'Loading  {sim_label} | {bond_label} ({don_res}→{acc_res}) …',
                  end=' ', flush=True)
            d, th = load_hbonds(path, don_res, acc_res,
                                donor_atom=don_atom, acc_atom=acc_atom,
                                qm_indices=qm_idx, mode=qm_mode)
            if args.dmin is not None:
                mask = d >= args.dmin
                d  = d[mask]
                th = th[mask] if th is not None else None
            per_sim.append((sim_label, d, th))
            print(f'{len(d)} bonds' + (' + angles' if th is not None else ', no angles'))
            if len(d):
                d_all.append(d)
            if th is not None and len(th):
                th_all.append(th)

        d_bins  = (np.linspace(np.concatenate(d_all).min(),
                               np.concatenate(d_all).max(),
                               args.bins + 1) if d_all else None)
        th_bins = (np.linspace(np.concatenate(th_all).min(),
                               np.concatenate(th_all).max(),
                               args.bins + 1) if th_all else None)

        for i, (sim_label, d, th) in enumerate(per_sim):
            color = COLORS[i % len(COLORS)]
            if len(d) and d_bins is not None:
                ax_d.hist(d, bins=d_bins, alpha=args.alpha, color=color,
                          label=sim_label, density=args.density)
                ax_d.axvline(np.mean(d), color=color, lw=1.5, ls='--')
            if th is not None and len(th) and th_bins is not None:
                ax_th.hist(th, bins=th_bins, alpha=args.alpha, color=color,
                           label=sim_label, density=args.density)
                ax_th.axvline(np.mean(th), color=color, lw=1.5, ls='--')

        ylabel = 'Density' if args.density else 'Count'

        ax_d.set_xlabel('D···A distance (Å)', fontsize=fs_l)
        ax_d.set_ylabel(ylabel, fontsize=fs_l)
        ax_d.set_title(f'{bond_label}  —  distance', fontsize=fs_t, pad=10)
        style_ax(ax_d, fs_l, fs_c)
        ax_d.legend(fontsize=fs_c)

        if th_all:
            ax_th.set_xlabel('D–H···A angle (°)', fontsize=fs_l)
            ax_th.set_ylabel(ylabel, fontsize=fs_l)
            ax_th.set_title(f'{bond_label}  —  angle', fontsize=fs_t, pad=10)
            style_ax(ax_th, fs_l, fs_c)
            ax_th.legend(fontsize=fs_c)
        else:
            ax_th.set_visible(False)

    fig.tight_layout(pad=1.5)

    if args.save:
        fig.savefig(args.save, dpi=args.dpi, bbox_inches='tight')
        print(f'Saved: {args.save}')
    else:
        plt.show()


if __name__ == '__main__':
    main()
