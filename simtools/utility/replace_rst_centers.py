#!/usr/bin/env python3
"""
Replace a placeholder value in AMBER rst files with per-window mean values,
and optionally generate a two-column window-map file for 2D umbrella sampling.

Typical workflow (2D umbrella prep):
  1. gen_rst.py --config cfg.json --start -1.2 --stop 1.2 --step 0.1
     (2nd restraint has rk=0,  monitoring only)
  2. Run 1D wham
  3. compute_window_means.py dumps/ --cols 7 --last 5000 --out window_means.dat
  4. gen_rst.py again (now 2nd restraint has umbrella=0, r2=r3=7.777 as placeholder, rk!=0)
  5. replace_rst_centers.py window_means.dat --col 7 --placeholder 7.777 --round 0.05
                            --axis2-start -1.2 --axis2-stop 1.2 --windows-out first_windows.dat
"""
import os
import math
import argparse


def round_to_step(val, step):
    """Round val to the nearest multiple of step (round-half-up)."""
    return math.floor(val / step + 0.5) * step


def decimal_places(step):
    """Infer number of decimal places needed from the rounding step."""
    if step >= 1.0:
        return 0
    return max(0, -int(math.floor(math.log10(step))))


def clamp_to_grid(val, start, stop, step):
    """
    Clamp val to [start, stop] first, then round to the nearest grid point.
    Values outside the range are moved to the boundary, not rounded toward it.
    """
    clamped = max(start, min(stop, val))
    rounded = round_to_step(clamped, step)
    # guard against float drift pushing rounded outside [start, stop]
    rounded = max(start, min(stop, rounded))
    return rounded, clamped != val


def val_to_win2(val, start, step):
    """Convert an axis2 value (already on-grid) to a 1-based window index."""
    return int(round((val - start) / step)) + 1


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Replace a placeholder in AMBER rst files with rounded per-window "
            "mean values, and optionally write a window-map file for 2D WHAM."
        )
    )
    parser.add_argument("means_file",
                        help="window_means.dat produced by compute_window_means.py")
    parser.add_argument("--col",          type=int, required=True,
                        help="Original dump column whose mean to use (e.g. --col 7 reads col7_mean)")
    parser.add_argument("--placeholder",  default="7.777",
                        help="String to replace in each rst file (default: 7.777)")
    parser.add_argument("--round",        type=float, default=0.05,
                        help="Rounding increment / axis2 step (default: 0.05)")
    parser.add_argument("--prefix",       default="wham_",
                        help="Window directory/file prefix (default: wham_)")
    parser.add_argument("--rst-suffix",   default="_rst.dat", dest="rst_suffix",
                        help="Rst filename suffix inside each window dir (default: _rst.dat)")
    parser.add_argument("--dir",          default="windows",
                        help="Root directory containing wham_N/ folders (default: windows)")
    # window-map options
    parser.add_argument("--axis2-start",  type=float, default=None, dest="axis2_start",
                        help="Axis2 range start (enables window-map output)")
    parser.add_argument("--axis2-stop",   type=float, default=None, dest="axis2_stop",
                        help="Axis2 range stop  (enables window-map output)")
    parser.add_argument("--windows-out",  default="first_windows.dat", dest="windows_out",
                        help="Output window-map file (default: first_windows.dat)")
    args = parser.parse_args()

    make_map = (args.axis2_start is not None and args.axis2_stop is not None)
    if (args.axis2_start is None) != (args.axis2_stop is None):
        parser.error("Provide both --axis2-start and --axis2-stop, or neither.")

    col_name = f"col{args.col}_mean"
    ndec     = decimal_places(args.round)

    # Parse means file
    with open(args.means_file) as fh:
        header_line = fh.readline().lstrip("# \t").split()
        if col_name not in header_line:
            raise ValueError(
                f"Column '{col_name}' not found in header.\n"
                f"Available: {header_line}"
            )
        col_idx = header_line.index(col_name)
        rows = [ln.split() for ln in fh
                if ln.strip() and not ln.strip().startswith("#")]

    print(f"Source   : {args.means_file}  (using {col_name})")
    print(f"Replace  : '{args.placeholder}'  ->  rounded to {args.round}")
    print(f"Rst files: {args.prefix}<label>/{args.prefix}<label>{args.rst_suffix}")
    if make_map:
        nwin2 = val_to_win2(args.axis2_stop, args.axis2_start, args.round)
        print(f"Axis2    : [{args.axis2_start}, {args.axis2_stop}] step {args.round}"
              f"  ({nwin2} windows)")
        print(f"Map out  : {args.windows_out}")
    print()

    n_ok = n_skip = 0
    map_rows = []

    for win1, parts in enumerate(rows, 1):
        label = parts[0]
        try:
            mean_val = float(parts[col_idx])
        except (IndexError, ValueError) as e:
            print(f"  Window {label:>8s}: cannot read mean ({e}), skipping")
            n_skip += 1
            continue

        if make_map:
            rounded, was_clamped = clamp_to_grid(
                mean_val, args.axis2_start, args.axis2_stop, args.round)
            win2 = val_to_win2(rounded, args.axis2_start, args.round)
            clamp_note = f"  [CLAMPED from {mean_val:.4f}]" if was_clamped else ""
        else:
            rounded    = round_to_step(mean_val, args.round)
            was_clamped = False
            clamp_note  = ""

        rounded_str = f"{rounded:.{ndec}f}"

        dirname  = os.path.join(args.dir, f"{args.prefix}{label}")
        filename = os.path.join(dirname, f"{args.prefix}{label}{args.rst_suffix}")

        if not os.path.isfile(filename):
            print(f"  Window {label:>8s}: {filename} not found, skipping")
            n_skip += 1
            continue

        with open(filename) as fh:
            content = fh.read()

        count = content.count(args.placeholder)
        if count == 0:
            print(f"  Window {label:>8s}: placeholder '{args.placeholder}' "
                  f"not found in {filename}, skipping")
            n_skip += 1
            continue

        with open(filename, "w") as fh:
            fh.write(content.replace(args.placeholder, rounded_str))

        if make_map:
            map_rows.append((win1, win2))
            print(f"  Window {label:>8s}: mean={mean_val:.4f}  ->  {rounded_str}"
                  f"  (win2={win2:>3d}){clamp_note}"
                  f"  ({count} substitution(s))")
        else:
            print(f"  Window {label:>8s}: mean={mean_val:.4f}  ->  {rounded_str}"
                  f"  ({count} substitution(s))")
        n_ok += 1

    print()
    print(f"Done: {n_ok} updated, {n_skip} skipped")

    if make_map and map_rows:
        with open(args.windows_out, "w") as fh:
            #fh.write("# window_rst1 window_rst2\n")
            for w1, w2 in map_rows:
                fh.write(f"{w1} {w2}\n")
        print(f"Window map saved: {args.windows_out}")


if __name__ == "__main__":
    main()
