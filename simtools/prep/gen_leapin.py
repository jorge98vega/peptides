#!/usr/bin/env python3
"""
gen_leapin.py — Generate tleap input files for AMBER nanotube systems.

Python replacement for gen_leapin.sh with added support for per-residue
overrides (mutations, LYS variants, GLY substitutions, …) at specific
positions in the sequence.

Usage:
    python gen_leapin.py --config myconfig.json [--output leap.in]

Config keys
-----------
pdbfile         str   Input PDB passed to loadpdbusingseq
outname         str   Base name for output .pdb / .top / .rst
ntubes          int   Number of tubes
nrings          int   Number of rings per tube
ring_residues   list  Residue names for one ring, e.g. ["LYN","PHD",…]
                      Pass a list of lists to cycle ring patterns (for
                      alternating sequences as in the 4t10s system).
overrides       dict  {"resid": "RESNAME"} for special positions.
                      Keys are 1-based global residue IDs (strings or ints).
ions            list  Ion residue names appended after all protein residues,
                      repeated once per tube, e.g. ["Cl-"] or ["TFA","TFA"].
water           bool  Append WAT after ions (default false)
leaprc          list  leaprc files to source
params          list  frcmod files  → loadamberparams
prep            list  prep/prepc files → loadamberprep
cyclic          bool  Generate N→C cyclic bond commands (default true)
box             list  [x, y, z] box dimensions in Å (fixed box, no solvation)
nocenter        bool  set default nocenter on (default true)
verbosity       int   tleap verbosity level (default 2)
solvate         dict  If present, use solvatebox instead of fixed box.
                      Keys: padding (float), waterbox (str, default TIP3PBOX),
                      add_ions (dict, e.g. {"Cl-": 180, "Na+": 0})

Example — 1t8s system with GLY mutations at positions 7, 11, 23, 43, 55, 59:
    {
        "pdbfile"      : "1t8s_1Cl_WAT_GLYa_preleap.pdb",
        "outname"      : "1t8s_1Cl_WAT_GLYa",
        "ntubes"       : 1,
        "nrings"       : 8,
        "ring_residues": ["LYN","PHD","LYN","PHD","LYN","PHD","LYN","PHD"],
        "overrides"    : {"27":"LYS","7":"GLY","11":"GLY","23":"GLY",
                          "43":"GLY","55":"GLY","59":"GLY"},
        "ions"         : ["Cl-"],
        "water"        : true,
        "leaprc"       : ["leaprc.protein.ff19SB","leaprc.water.tip3p"],
        "params"       : ["frcmod.ionsff99_tip3p","frcmod.tip3p"],
        "prep"         : ["PHD.prep","TYD.prep"],
        "cyclic"       : true,
        "box"          : [80.0, 80.0, 80.0],
        "nocenter"     : true
    }

Example — 9t10s system with alternating ring patterns and TFA ions:
    {
        "pdbfile"      : "9t10s.pdb",
        "outname"      : "9t10s_run01",
        "ntubes"       : 9,
        "nrings"       : 10,
        "ring_residues": [
            ["LYS","PHD","LYN","PHD","LYS","PHD","LYN","PHD"],
            ["LYN","PHD","LYS","PHD","LYN","PHD","LYS","PHD"]
        ],
        "overrides"    : {},
        "ions"         : ["TFA","TFA","TFA","TFA","TFA",
                          "TFA","TFA","TFA","TFA","TFA",
                          "TFA","TFA","TFA","TFA","TFA",
                          "TFA","TFA","TFA","TFA","TFA"],
        "leaprc"       : ["leaprc.protein.ff19SB","leaprc.water.tip3p"],
        "params"       : ["frcmod.ionsff99_tip3p","frcmod.tip3p"],
        "prep"         : ["PHD.prep","TYD.prep","TFA.prepc"],
        "cyclic"       : true,
        "solvate"      : {"padding": 15.0, "add_ions": {"Cl-": 180, "Na+": 0}}
    }
"""

import argparse
import json
import os
import sys


# ── Sequence generation ───────────────────────────────────────────────────────

def _ring_pattern(ring_residues, ring_idx):
    """Return the residue list for ring_idx, cycling if ring_residues is a
    list of lists."""
    if ring_residues and isinstance(ring_residues[0], list):
        return ring_residues[ring_idx % len(ring_residues)]
    return ring_residues


def build_sequence(ntubes, nrings, ring_residues, overrides, ions, water):
    """Return the ordered residue lines for the loadpdbusingseq block."""
    ring_sz = len(_ring_pattern(ring_residues, 0))
    lines = []

    # Protein: all tubes, each tube's rings in order
    for t in range(ntubes):
        for r in range(nrings):
            pattern = _ring_pattern(ring_residues, r)
            row = []
            for p in range(ring_sz):
                resid = t * nrings * ring_sz + r * ring_sz + p + 1
                row.append(overrides.get(str(resid), pattern[p]))
            lines.append(' '.join(row))

    # Ions: once per tube, after all protein residues
    for _t in range(ntubes):
        for ion in ions:
            lines.append(ion)

    if water:
        lines.append('WAT')

    return lines


def build_bonds(ntubes, nrings, ring_sz):
    """Return cyclic N→C bond commands for every ring."""
    bonds = []
    for t in range(ntubes):
        for r in range(nrings):
            base  = (t * nrings + r) * ring_sz
            first = base + 1
            last  = base + ring_sz
            bonds.append(f'bond x.{first}.N x.{last}.C')
    return bonds


# ── leap.in assembly ──────────────────────────────────────────────────────────

def generate(cfg):
    ntubes      = cfg['ntubes']
    nrings      = cfg['nrings']
    ring_r      = cfg['ring_residues']
    ring_sz     = len(_ring_pattern(ring_r, 0))
    overrides   = {str(k): v for k, v in cfg.get('overrides', {}).items()}
    ions        = cfg.get('ions', [])
    water       = cfg.get('water', False)
    cyclic      = cfg.get('cyclic', True)
    box         = cfg.get('box', None)
    nocenter    = cfg.get('nocenter', True)
    verbosity   = cfg.get('verbosity', 2)
    leaprc      = cfg.get('leaprc', ['leaprc.protein.ff19SB'])
    params      = cfg.get('params', [])
    prep        = cfg.get('prep', [])
    solvate     = cfg.get('solvate', None)
    outname     = cfg['outname']

    seq_lines   = build_sequence(ntubes, nrings, ring_r, overrides, ions, water)
    bond_lines  = build_bonds(ntubes, nrings, ring_sz) if cyclic else []

    out = []

    for rc in leaprc:
        out.append(f'source {rc}')
    out.append(f'verbosity {verbosity}')
    for p in params:
        out.append(f'loadamberparams {p}')
    for p in prep:
        out.append(f'loadamberprep {p}')

    out.append(f'x = loadpdbusingseq {cfg["pdbfile"]} {{')
    out.extend(seq_lines)
    out.append('')
    out.append('')
    out.append('}')

    out.extend(bond_lines)

    if solvate:
        wbox    = solvate.get('waterbox', 'TIP3PBOX')
        padding = solvate.get('padding', 15.0)
        out.append(f'solvatebox x {wbox} {padding:.1f} 2.0')
        for ion, n in solvate.get('add_ions', {}).items():
            out.append(f'addions x {ion} {n}')
    elif box:
        out.append(f'set x box {{ {box[0]:.1f}  {box[1]:.1f}  {box[2]:.1f} }}')
        if nocenter:
            out.append('set default nocenter on')

    out.append('charge x')
    out.append(f'savepdb x {outname}.pdb')
    out.append(f'saveamberparm x {outname}.top {outname}.rst')

    return '\n'.join(out) + '\n'


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', required=True,
                        help='JSON configuration file')
    parser.add_argument('--output', default=None,
                        help='Output path (default: leap_{outname}.in)')
    args = parser.parse_args()

    with open(args.config) as fh:
        cfg = json.load(fh)

    content  = generate(cfg)
    outpath  = args.output or f'leap_{cfg["outname"]}.in'

    with open(outpath, 'w') as fh:
        fh.write(content)

    ring_sz = len(_ring_pattern(cfg['ring_residues'], 0))
    nres    = cfg['ntubes'] * cfg['nrings'] * ring_sz
    ov      = {str(k): v for k, v in cfg.get('overrides', {}).items()}

    print(f'Written  : {outpath}')
    print(f'System   : {cfg["ntubes"]} tube(s) × {cfg["nrings"]} rings '
          f'× {ring_sz} residues = {nres} protein residues')
    if ov:
        items = ', '.join(f'{k}:{v}' for k, v in
                          sorted(ov.items(), key=lambda x: int(x[0])))
        print(f'Overrides: {items}')


if __name__ == '__main__':
    main()
