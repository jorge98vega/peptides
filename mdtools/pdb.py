"""
pdb.py — PDB reader/writer for AMBER-generated structures.

Handles the two column layouts produced by AMBER tools:
  standard  resname at col 17  tleap savepdb, ambpdb
  preleap   resname at col 18  legacy prep scripts (substitute_res, positionCls, …)
The format is detected automatically from the file content.

Public API
----------
Atom                         dataclass for one ATOM/HETATM record
read_pdb(path)               → list[Atom]  (ATOM/HETATM only)
write_pdb(path, atoms)       list[Atom] → file, serials renumbered from 1
read_records(path)           → list[Atom | str], all lines in order
write_records(path, records) round-trip; non-Atom strings written verbatim
to_arrays(atoms)             → (names, resnames, resids, xyz) as numpy arrays
from_arrays(names, resnames, resids, xyz, occ=None, bfac=None) → list[Atom]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union

import numpy as np


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Atom:
    """One ATOM/HETATM record."""
    serial:  int
    name:    str
    resname: str
    resid:   int
    x: float
    y: float
    z: float
    occ:  float = 0.0
    bfac: float = 0.0

    @property
    def pos(self) -> np.ndarray:
        """xyz as a (3,) array."""
        return np.array([self.x, self.y, self.z])


Record = Union[Atom, str]   # str for TER / END / CRYST1 / REMARK / …


# ── Format detection ──────────────────────────────────────────────────────────

def _rncol(lines: List[str]) -> int:
    """
    Return the 0-based column where resname starts.
    17 → standard PDB (tleap / ambpdb)
    18 → preleap format (substitute_res.py, positionCls.py, …)
    """
    for line in lines:
        if line.startswith(('ATOM', 'HETATM')):
            return 17 if line[17:18].strip() else 18
    return 18   # fallback


# ── Line-level parsing / formatting ──────────────────────────────────────────

def _parse(line: str, rn_col: int) -> Atom:
    """Parse one ATOM/HETATM line given the resname column offset."""
    occ_s  = line[54:60].strip()
    bfac_s = line[60:66].strip()
    return Atom(
        serial  = int(line[6:11]),
        name    = line[13:17].strip(),
        resname = line[rn_col:rn_col + 3].strip(),
        resid   = int(line[22:26]),
        x       = float(line[30:38]),
        y       = float(line[38:46]),
        z       = float(line[46:54]),
        occ     = float(occ_s)  if occ_s  else 0.0,
        bfac    = float(bfac_s) if bfac_s else 0.0,
    )


def _format(a: Atom, serial: int) -> str:
    """Format an Atom as a PDB ATOM line (preleap column layout)."""
    return (
        f"ATOM  {serial:5d}  {a.name:<4} {a.resname:<3} {a.resid:4d}    "
        f"{a.x:8.3f}{a.y:8.3f}{a.z:8.3f}"
        f"  {a.occ:.2f}  {a.bfac:.2f}\n"
    )


# ── Public I/O ────────────────────────────────────────────────────────────────

def read_pdb(path: str) -> List[Atom]:
    """
    Parse ATOM/HETATM lines; all other lines are discarded.
    Both standard and preleap column layouts are handled automatically.
    """
    with open(path) as fh:
        lines = fh.readlines()
    rn = _rncol(lines)
    return [_parse(l, rn) for l in lines if l.startswith(('ATOM', 'HETATM'))]


def write_pdb(path: str, atoms: List[Atom]) -> None:
    """
    Write atoms to path in preleap column format.
    Serials are renumbered from 1; a trailing END line is added.
    TER placement is left to the caller — use write_records for that.
    """
    with open(path, 'w') as fh:
        for serial, a in enumerate(atoms, 1):
            fh.write(_format(a, serial))
        fh.write('END   \n')


def read_records(path: str) -> List[Record]:
    """
    Parse all lines preserving their order.
    ATOM/HETATM → Atom objects; everything else → raw string (newline stripped).
    Use this when TER / END / CRYST1 lines must be kept in place.
    """
    with open(path) as fh:
        lines = fh.readlines()
    rn = _rncol(lines)
    out: List[Record] = []
    for line in lines:
        if line.startswith(('ATOM', 'HETATM')):
            out.append(_parse(line, rn))
        else:
            out.append(line.rstrip('\n'))
    return out


def write_records(path: str, records: List[Record]) -> None:
    """
    Write records to path.
    Atom serials are renumbered from 1; non-Atom strings are written verbatim.
    """
    serial = 0
    with open(path, 'w') as fh:
        for r in records:
            if isinstance(r, Atom):
                serial += 1
                fh.write(_format(r, serial))
            else:
                fh.write(r + '\n')


# ── Array helpers (compatible with legacy prep scripts) ───────────────────────

def to_arrays(atoms: List[Atom]):
    """
    Return (names, resnames, resids, xyz) as numpy arrays.
    Drop-in replacement for the parallel-list interface used in
    substitute_res.py, positionCls.py, and prep_pdb.py.
    """
    names    = np.array([a.name    for a in atoms])
    resnames = np.array([a.resname for a in atoms])
    resids   = np.array([a.resid   for a in atoms], dtype=int)
    xyz      = np.array([[a.x, a.y, a.z] for a in atoms])
    return names, resnames, resids, xyz


def from_arrays(names, resnames, resids, xyz,
                occ=None, bfac=None) -> List[Atom]:
    """
    Build list[Atom] from parallel arrays.
    occ and bfac default to 0.0 when not supplied.
    """
    n    = len(names)
    occ  = occ  if occ  is not None else [0.0] * n
    bfac = bfac if bfac is not None else [0.0] * n
    return [
        Atom(
            serial  = i + 1,
            name    = str(names[i]),
            resname = str(resnames[i]),
            resid   = int(resids[i]),
            x       = float(xyz[i, 0]),
            y       = float(xyz[i, 1]),
            z       = float(xyz[i, 2]),
            occ     = float(occ[i]),
            bfac    = float(bfac[i]),
        )
        for i in range(n)
    ]
