"""Tests for utility/gen_rst.py"""

import re
import sys
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "utility" / "gen_rst.py"
DATA   = Path(__file__).parent / "data" / "gen_rst"


# --- helpers -----------------------------------------------------------------

def run(tmp_path, config, extra_args=()):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(config), *extra_args],
        capture_output=True, text=True, cwd=str(tmp_path)
    )
    return result


def parse_rst(path):
    """Return list of dicts, one per &rst block: r1,r2,r3,r4,rk2,rk3,iat."""
    blocks = []
    for block in re.split(r"&end", Path(path).read_text()):
        if "&rst" not in block:
            continue
        d = {}
        for key in ("r1", "r2", "r3", "r4", "rk2", "rk3"):
            m = re.search(rf"{key}=\s*(-?[\d.]+)", block)
            if m:
                d[key] = float(m.group(1))
        m = re.search(r"iat=([\d,]+)", block)
        if m:
            d["iat"] = [int(x) for x in m.group(1).split(",") if x]
        blocks.append(d)
    return blocks


def approx(val, expected, tol=1e-3):
    return abs(val - expected) < tol


# --- single rst (equilibration) ----------------------------------------------

def test_single_creates_one_window(tmp_path):
    r = run(tmp_path, DATA / "single.json")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "wham_1" / "wham_1_rst.dat").exists()
    assert not (tmp_path / "wham_2").exists()


def test_single_override_r_values(tmp_path):
    run(tmp_path, DATA / "single.json")
    blocks = parse_rst(tmp_path / "wham_1" / "wham_1_rst.dat")

    # restraint 1: all four r-values overridden in JSON
    assert approx(blocks[0]["r1"], 0.0)
    assert approx(blocks[0]["r2"], 0.0)
    assert approx(blocks[0]["r3"], 3.5)
    assert approx(blocks[0]["r4"], 5.0)
    assert approx(blocks[0]["rk2"], 400.0)

    # restraint 2: no overrides → defaults (center=0)
    assert approx(blocks[1]["r1"], -500.0)
    assert approx(blocks[1]["r2"],    0.0)
    assert approx(blocks[1]["r3"],    0.0)
    assert approx(blocks[1]["r4"],  500.0)
    assert approx(blocks[1]["rk2"],   0.0)


def test_single_iat(tmp_path):
    run(tmp_path, DATA / "single.json")
    blocks = parse_rst(tmp_path / "wham_1" / "wham_1_rst.dat")
    assert blocks[0]["iat"] == [550, 1315]
    assert blocks[1]["iat"] == [797, 1315]


# --- WHAM 1D -----------------------------------------------------------------

WHAM1D_ARGS = ["--start", "-1.0", "--stop", "1.0", "--step", "0.5"]


def test_wham1d_window_count(tmp_path):
    r = run(tmp_path, DATA / "wham1d.json", WHAM1D_ARGS)
    assert r.returncode == 0, r.stderr
    dirs = sorted(tmp_path.glob("wham_*"))
    assert len(dirs) == 5   # -1.0, -0.5, 0.0, 0.5, 1.0


def test_wham1d_output_names(tmp_path):
    run(tmp_path, DATA / "wham1d.json", WHAM1D_ARGS)
    for i in range(1, 6):
        assert (tmp_path / f"wham_{i}" / f"wham_{i}_rst.dat").exists()


def test_wham1d_centers(tmp_path):
    run(tmp_path, DATA / "wham1d.json", WHAM1D_ARGS)
    expected_centers = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for i, center in enumerate(expected_centers, 1):
        blocks = parse_rst(tmp_path / f"wham_{i}" / f"wham_{i}_rst.dat")
        # first restraint is diff (scanned): r2=r3=center
        assert approx(blocks[0]["r2"], center), f"window {i}: r2 expected {center}"
        assert approx(blocks[0]["r3"], center), f"window {i}: r3 expected {center}"
        # default walls
        assert approx(blocks[0]["r1"], -500.0)
        assert approx(blocks[0]["r4"],  500.0)


def test_wham1d_monitoring_restraint(tmp_path):
    run(tmp_path, DATA / "wham1d.json", WHAM1D_ARGS)
    # second restraint (monitoring) has rk=0 in every window
    for i in range(1, 6):
        blocks = parse_rst(tmp_path / f"wham_{i}" / f"wham_{i}_rst.dat")
        assert approx(blocks[1]["rk2"], 0.0)


# --- WHAM 2D -----------------------------------------------------------------

WHAM2D_ARGS = [
    "--start", "0.0", "--stop", "1.0", "--step", "1.0",
    "--axis2-start", "0.0", "--axis2-stop", "2.0", "--axis2-step", "1.0",
]


def test_wham2d_window_count(tmp_path):
    r = run(tmp_path, DATA / "wham2d.json", WHAM2D_ARGS)
    assert r.returncode == 0, r.stderr
    dirs = sorted(tmp_path.glob("wham_*_*"))
    assert len(dirs) == 6   # 2 × 3


def test_wham2d_output_names(tmp_path):
    run(tmp_path, DATA / "wham2d.json", WHAM2D_ARGS)
    for i in range(1, 3):
        for j in range(1, 4):
            assert (tmp_path / f"wham_{i}_{j}" / f"wham_{i}_{j}_rst.dat").exists()


def test_wham2d_fixed_tracks_axis1(tmp_path):
    run(tmp_path, DATA / "wham2d.json", WHAM2D_ARGS)
    # fixed restraint (index 0) should have r2=r3=axis1_center regardless of j
    axis1_centers = {1: 0.0, 2: 1.0}
    for i, c1 in axis1_centers.items():
        for j in range(1, 4):
            blocks = parse_rst(tmp_path / f"wham_{i}_{j}" / f"wham_{i}_{j}_rst.dat")
            assert approx(blocks[0]["r2"], c1), f"wham_{i}_{j}: fixed r2 expected {c1}"
            assert approx(blocks[0]["r3"], c1), f"wham_{i}_{j}: fixed r3 expected {c1}"


def test_wham2d_variable_tracks_axis2(tmp_path):
    run(tmp_path, DATA / "wham2d.json", WHAM2D_ARGS)
    # variable restraint (index 1) should have r2=r3=axis2_center regardless of i
    axis2_centers = {1: 0.0, 2: 1.0, 3: 2.0}
    for i in range(1, 3):
        for j, c2 in axis2_centers.items():
            blocks = parse_rst(tmp_path / f"wham_{i}_{j}" / f"wham_{i}_{j}_rst.dat")
            assert approx(blocks[1]["r2"], c2), f"wham_{i}_{j}: variable r2 expected {c2}"
            assert approx(blocks[1]["r3"], c2), f"wham_{i}_{j}: variable r3 expected {c2}"


def test_wham2d_incomplete_axis2_args_fails(tmp_path):
    r = run(tmp_path, DATA / "wham2d.json",
            ["--axis2-start", "0.0", "--axis2-stop", "1.0"])  # missing --axis2-step
    assert r.returncode != 0
