# peptides — MD simulation toolkit for cyclic peptide nanotubes

Tools for building, running, and analysing AMBER MD simulations of
cyclic peptide nanotube systems (LYN/PHD alternating rings, multi-tube assemblies).

---

## Package layout

```
peptides/
├── mdtools/          analysis library (Python package, conda env required)
├── simtools/
│   ├── prep/         structure preparation scripts
│   ├── utility/      WHAM workflow utilities
│   ├── analysis/     plotting and QC scripts
│   ├── run/          SLURM job scripts (FAST05 / CESGA)
│   ├── tcl/          VMD visualisation scripts
│   └── inputs/       example JSON config files
└── legacy/           old scripts kept for reference (not maintained)
```

---

## mdtools/

Python package for trajectory analysis. Requires the conda environment
(`pandas`, `mdtraj`, `seaborn`, …). Import as `from mdtools import ...`.

| Module | What it does |
|--------|--------------|
| `pdb.py` | Lightweight PDB reader/writer (numpy only). Auto-detects preleap vs standard AMBER column layouts. Public API: `read_pdb`, `write_pdb`, `read_records`, `write_records`, `to_arrays`, `from_arrays`, `Atom`. |
| `core.py` | Trajectory loading, orientation, CA-based geometric analysis |
| `analysis.py` | Per-frame observables: H-bonds, distances, water indices |
| `statistics.py` | Ensemble averaging, error estimation |
| `visualization.py` | Figure helpers (seaborn/matplotlib wrappers) |

---

## simtools/prep/ — structure preparation

### New scripts (JSON-config driven)

| Script | What it does | Inputs | Outputs |
|--------|-------------|--------|---------|
| `prep_pdb.py` | Clean and/or clone a nanotube PDB: renumber atoms/residues, apply per-clone translation + Z rotation | `--config` JSON (`pdbfile`, `newfile`, `Nrings`, `Nres`, `Natoms`, `clones[]`) | single PDB |
| `mutate_residues.py` | Strip sidechains at specified residues and rename (e.g. LYN→GLY) | `--input PDB --output PDB --resids 7,11,23 --from LYN --to GLY` | PDB |
| `gen_leapin.py` | Generate tleap `.in` input from a JSON config. Supports multi-tube, alternating ring patterns, per-residue overrides, fixed box or solvation | `--config` JSON (see script docstring) | `leap_<outname>.in` |

### Legacy scripts (hardcoded paths, kept for reference)

| Script | What it does |
|--------|-------------|
| `substitute_res.py` | Replace all occurrences of one residue with atoms from a template PDB (used to place TFA ions) |
| `positionCls.py` | Position Cl⁻ ions near LYS NZ atoms based on HZ centroid |

### Force-field and topology files

| File | Purpose |
|------|---------|
| `PHD.prep`, `TYD.prep`, `TFA.prepc` | AMBER prep/prepc for non-standard residues |
| `frcmod.ionsff99_tip3p`, `frcmod.tip3p` | frcmod parameter files |
| `TFA-.pdb`, `TP3.pdb` | Template PDBs for TFA and TIP3P water |
| `models/` | Pre-built ideal nanotube PDB geometries (1/4/9 tubes × 6/8/10 rings) |

---

## simtools/utility/ — WHAM workflow

These scripts implement the 4-step pipeline from 1D umbrella sampling to 2D WHAM.

| Script | What it does | Inputs | Outputs |
|--------|-------------|--------|---------|
| `gen_rst.py` | Generate AMBER restraint files for 1D or 2D umbrella sampling grids | `--config` JSON, `--start/--stop/--step`, optional `--axis2-*` | `windows/wham_N/wham_N_rst.dat` (1D) or `windows/wham_i_j/…` (2D) |
| `compute_window_means.py` | Compute per-window mean ± std from AMBER dump files | dump directory, `--cols`, `--last N` | `window_means.dat` |
| `replace_rst_centers.py` | Replace placeholder value in rst files with rounded per-window means; write axis2 window map | `window_means.dat`, `--col`, `--placeholder`, `--round`, optional `--axis2-*` | updated rst files, `first_windows.dat` |
| `wham_status.py` | SLURM grid visualiser — colour-coded status table for all windows | SLURM queue + dump files; optional `failed_windows.dat` | terminal display |
| `reorientate_rst.py` | Rotate a trajectory/PDB to align nanotube axis along Z | `rst`\|`pdb` format, folder, traj name | `*_oriented.rst/pdb` |
| `plot_rst.py` | Plot restraint time series from dump files | dump directory | matplotlib figure |
| `node_runtimes.py` | Parse SLURM logs to compare per-node GPU runtimes | — | terminal table |
| `recenter_rst.sh` | Wrap and recenter an rst structure using cpptraj | — | recentered rst |
| `concat_windows.sh` | Concatenate per-window trajectories for cpptraj | — | merged nc |
| `merge_netcdf.sh` | Merge multiple NetCDF files | — | merged nc |
| `Hsampling.jl` / `restrainer.jl` | Julia scripts for H-bond and distance sampling | — | dump files |

---

## simtools/analysis/ — plotting and QC

| Script | What it does |
|--------|-------------|
| `plot_wham.py` | Plot 1D PMF from WHAM output |
| `plot_wham2d.py` | 2D PMF heatmap |
| `check_wham2d.py` | QC heatmaps: mean deviation from target restraints + z-score anomaly per window; writes `failed_windows.dat` |
| `plot_restraints.py` | Time-series plots of restrained coordinates across all windows |
| `plot_histograms.py` | Coordinate histograms per window (overlap check) |
| `plot_hbond_hists.py` | H-bond occupancy histograms |
| `plot_coord_hists.py` | General coordinate distribution histograms |
| `plot_map.py` | 2D scatter/map of sampled coordinate space |
| `extract_ucell.py` | Extract unit-cell frames from MD supercell for DFT input (xyz with Lattice header) |
| `get_water_indices.py` | Find water residue indices inside the nanotube channel |
| `wham1d.sh` / `wham2d.sh` | Run the WHAM executable (Alan Grossfield's wham) |
| `gen_cp2k_inputs.py` | Generate CP2K input files from extracted frames |
| `cp2k_pdos.py` / `cp2k_pdos2dat.sh` | Process CP2K projected DOS output |
| `plot_dos_*.py` | Plot electronic DOS from CP2K / Fireball / Gaussian |
| `distances_stats.sh` | Shell wrapper for distance statistics via cpptraj |

---

## simtools/run/ — job scripts

Cluster-specific SLURM scripts for the standard MD pipeline:

```
0-min  →  1-heat  →  2-equil  →  3-prod  →  [4-qmmm / wham / mmpbsa]
```

Two clusters: `FAST05/` and `CESGA/`. Each stage has a `MD_*.sh` (AMBER input)
and a `run_*.sh` (SLURM submission). The `wham-2d/` subfolder has array-job
scripts for running all windows in parallel.

---

## Typical workflows

### 1. Build a new topology

```
models/*.pdb          ideal geometry
      │
      ▼
prep_pdb.py           clean + clone to N tubes    →  system_preleap.pdb
      │
      ├── [optional] mutate_residues.py            →  system_GLY_preleap.pdb
      │               strip LYN sidechains, rename
      │
      ├── [optional] substitute_res.py / positionCls.py  (legacy, for TFA/Cl-)
      │
      ▼
gen_leapin.py         JSON config → leap_*.in
      │
      ▼
tleap                                              →  system.top + system.rst
```

### 2. 1D umbrella sampling → 2D WHAM

```
gen_rst.py  --start … --stop … --step …           →  windows/wham_N/wham_N_rst.dat
      │
      ▼
run_array_wham2d.sh   (SLURM, 1D pass)            →  wham_N_rst_1.dump
      │
      ▼
compute_window_means.py --cols 2 …                →  window_means.dat
      │
      ▼
replace_rst_centers.py  --col 2 --placeholder …   →  updated rst files
                         --axis2-start … --stop …     first_windows.dat
      │
      ▼
gen_rst.py  --axis2-* …                           →  windows/wham_i_j/wham_i_j_rst.dat
      │
      ▼
run_array_wham2d.sh   (SLURM, 2D pass)
      │
      ▼
check_wham2d.py       QC heatmaps                 →  failed_windows.dat
      │
      ▼
wham2d.sh             run WHAM executable         →  pmf2d.dat
      │
      ▼
plot_wham2d.py        visualise PMF
```
