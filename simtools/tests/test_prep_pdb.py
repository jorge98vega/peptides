"""
Tests for prep/prep_pdb.py

Synthetic tests run out of the box.
Data-driven tests require placing a real PDB and config in tests/data/prep_pdb/:
    input.pdb, clean.json, clone.json
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT  = Path(__file__).parent.parent / "prep" / "prep_pdb.py"
DATA    = Path(__file__).parent / "data" / "prep_pdb"
OUTPUTS = Path(__file__).parent / "outputs" / "prep_pdb"


# --- helpers -----------------------------------------------------------------

def make_test_pdb(path, Nrings, Nres, Natoms):
    """Generate a minimal synthetic PDB with non-sequential residue IDs (to test renumbering)."""
    atoms_per_res = Natoms // Nres
    atid = 0
    orig_resid = 100
    with open(path, "w") as f:
        for ring in range(Nrings):
            for res in range(Nres):
                orig_resid += 1
                for a in range(atoms_per_res):
                    atid += 1
                    x, y, z = float(ring * 10), float(res * 3), float(a)
                    f.write(
                        f"ATOM  {atid:5d}  CA  ALA {orig_resid:4d}    "
                        f"{x:8.3f}{y:8.3f}{z:8.3f}  0.00  0.00\n"
                    )
        f.write("END\n")


def run_script(config, tmp_path):
    cfg_path = tmp_path / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(config, f)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(cfg_path)],
        capture_output=True, text=True
    )
    return result


def check_output(pdb_path, Nrings, Natoms, Nres, n_clones):
    lines = Path(pdb_path).read_text().splitlines()
    atom_lines = [l for l in lines if l.startswith("ATOM")]
    ter_lines  = [l for l in lines if l.startswith("TER")]
    end_lines  = [l for l in lines if l.startswith("END")]

    assert len(atom_lines) == n_clones * Nrings * Natoms, \
        f"Expected {n_clones * Nrings * Natoms} ATOM lines, got {len(atom_lines)}"
    assert len(ter_lines) == n_clones * Nrings, \
        f"Expected {n_clones * Nrings} TER lines, got {len(ter_lines)}"
    assert len(end_lines) == 1, "Expected exactly one END line"

    # Residue renumbering: first clone should start at 1, end at Nrings*Nres
    first_clone_atoms = atom_lines[:Nrings * Natoms]
    resids = [int(l[22:26]) for l in first_clone_atoms]
    assert resids[0] == 1, f"First residue should be 1, got {resids[0]}"
    assert resids[-1] == Nrings * Nres, \
        f"Last residue in first clone should be {Nrings * Nres}, got {resids[-1]}"


# --- synthetic tests (no external files needed) ------------------------------

NRINGS = 4
NRES   = 2
NATOMS = 6  # 3 atoms per residue

@pytest.fixture
def synthetic_pdb(tmp_path):
    pdb = tmp_path / "input.pdb"
    make_test_pdb(pdb, NRINGS, NRES, NATOMS)
    return pdb


def test_clean_mode(synthetic_pdb, tmp_path):
    output = tmp_path / "output.pdb"
    cfg = {
        "pdbfile": str(synthetic_pdb),
        "newfile": str(output),
        "Nrings": NRINGS, "Nres": NRES, "Natoms": NATOMS
    }
    result = run_script(cfg, tmp_path)
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    assert output.exists()
    check_output(output, NRINGS, NATOMS, NRES, n_clones=1)


def test_clone_mode(synthetic_pdb, tmp_path):
    output = tmp_path / "output.pdb"
    clones = [
        {"translation": [0.0,  0.0,  0.0], "angle":  0.0},
        {"translation": [22.0, 0.0,  0.0], "angle": 10.0},
        {"translation": [22.0, 22.0, 0.0], "angle": 10.0},
        {"translation": [0.0,  22.0, 0.0], "angle": 10.0},
    ]
    cfg = {
        "pdbfile": str(synthetic_pdb),
        "newfile": str(output),
        "Nrings": NRINGS, "Nres": NRES, "Natoms": NATOMS,
        "clones": clones
    }
    result = run_script(cfg, tmp_path)
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    assert output.exists()
    check_output(output, NRINGS, NATOMS, NRES, n_clones=len(clones))


def test_missing_atoms_raises(synthetic_pdb, tmp_path):
    """Script should fail if Ntotal > atoms in file."""
    output = tmp_path / "output.pdb"
    cfg = {
        "pdbfile": str(synthetic_pdb),
        "newfile": str(output),
        "Nrings": NRINGS * 10,  # far more than available
        "Nres": NRES, "Natoms": NATOMS
    }
    result = run_script(cfg, tmp_path)
    assert result.returncode != 0


# --- data-driven tests (require files in tests/data/prep_pdb/) ---------------

def _data_file(name):
    path = DATA / name
    missing = not path.exists() or not (DATA / "input.pdb").exists()
    return pytest.param(path, marks=pytest.mark.skipif(
        missing, reason=f"data file(s) missing in tests/data/prep_pdb/ (need {name} + input.pdb)"
    ))


@pytest.mark.parametrize("config_path", [_data_file("clean.json")])
def test_clean_real(config_path, tmp_path):
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with open(config_path) as f:
        cfg = json.load(f)
    cfg["pdbfile"] = str(DATA / cfg["pdbfile"])
    cfg["newfile"] = str(OUTPUTS / Path(cfg["newfile"]).name)
    result = run_script(cfg, tmp_path)
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    check_output(cfg["newfile"], cfg["Nrings"], cfg["Natoms"], cfg["Nres"], n_clones=1)


@pytest.mark.parametrize("config_path", [_data_file("clone.json")])
def test_clone_real(config_path, tmp_path):
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with open(config_path) as f:
        cfg = json.load(f)
    cfg["pdbfile"] = str(DATA / cfg["pdbfile"])
    cfg["newfile"] = str(OUTPUTS / Path(cfg["newfile"]).name)
    n_clones = len(cfg.get("clones", [{}]))
    result = run_script(cfg, tmp_path)
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    check_output(cfg["newfile"], cfg["Nrings"], cfg["Natoms"], cfg["Nres"], n_clones=n_clones)
