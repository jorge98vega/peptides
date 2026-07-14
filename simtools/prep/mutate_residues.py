#!/usr/bin/env python3
"""
mutate_residues.py — Strip sidechains from specified residues and rename them.

Reads any AMBER PDB (both standard and preleap column layouts handled
automatically via mdtools.pdb).  For each target residue ID, keeps only the
atoms appropriate for the new residue type, renames the residue, and writes
a clean output PDB ready for tleap / loadpdbusingseq.

Usage:
    python mutate_residues.py --input in.pdb --output out.pdb \\
        --resids 7,11,23,43 --from LYN --to GLY

    # Override the atom set to keep:
    python mutate_residues.py ... --keep N,H,CA,HA,CB,C,O

    # Chain multiple passes for mixed targets:
    python mutate_residues.py --input in.pdb --output tmp.pdb \\
        --resids 7,11 --from LYN --to GLY
    python mutate_residues.py --input tmp.pdb --output out.pdb \\
        --resids 23,43 --from LYN --to ALA

Built-in atom sets (LEaP builds the missing hydrogens):
    GLY  N H CA C O              LEaP adds HA2 HA3
    ALA  N H CA HA CB C O        LEaP adds HB1 HB2 HB3
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))
from mdtools.pdb import read_records, write_records, Atom

# Atoms to keep for each supported target residue type.
# Names must match those present in the source residue (AMBER convention).
KEEP = {
    'GLY': {'N', 'H', 'CA', 'C', 'O'},
    'ALA': {'N', 'H', 'CA', 'HA', 'CB', 'C', 'O'},
}


def mutate(records, resids, from_res, to_res, keep):
    out = []
    for r in records:
        if not isinstance(r, Atom):
            out.append(r)
            continue
        if r.resid in resids:
            if r.resname != from_res:
                raise ValueError(
                    f'Residue {r.resid} is {r.resname!r}, expected {from_res!r}')
            if r.name not in keep:
                continue
            r.resname = to_res
        out.append(r)
    return out


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input',  required=True,
                        help='Input PDB file')
    parser.add_argument('--output', required=True,
                        help='Output PDB file')
    parser.add_argument('--resids', required=True,
                        help='Comma-separated 1-based residue IDs to mutate')
    parser.add_argument('--from',   required=True, dest='from_res',
                        help='Source residue name (e.g. LYN)')
    parser.add_argument('--to',     required=True, dest='to_res',
                        help='Target residue name (e.g. GLY)')
    parser.add_argument('--keep',   default=None,
                        help='Comma-separated atom names to keep '
                             '(overrides the built-in set for --to)')
    args = parser.parse_args()

    resids = {int(x) for x in args.resids.split(',')}

    if args.keep:
        keep = set(args.keep.split(','))
    elif args.to_res in KEEP:
        keep = KEEP[args.to_res]
    else:
        keep = {'N', 'H', 'CA', 'C', 'O'}
        print(f'Warning: no built-in atom set for {args.to_res!r}, '
              f'using backbone only. Pass --keep to override.')

    records = read_records(args.input)
    n_before = sum(isinstance(r, Atom) for r in records)

    records = mutate(records, resids, args.from_res, args.to_res, keep)
    n_after  = sum(isinstance(r, Atom) for r in records)

    write_records(args.output, records)

    print(f'Input   : {args.input}  ({n_before} atoms)')
    print(f'Output  : {args.output}  ({n_after} atoms, '
          f'{n_before - n_after} removed)')
    print(f'Mutated : {args.from_res}→{args.to_res} at residues {sorted(resids)}')
    print(f'Kept    : {sorted(keep)}')


if __name__ == '__main__':
    main()
