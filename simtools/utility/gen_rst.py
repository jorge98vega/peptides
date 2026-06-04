#!/usr/bin/env python3
import os
import json
import argparse


class Restraint:
    DEFAULT_RSTWT = {
        "distance": None,
        "angle":    None,
        "diff":     [1.0, -1.0],
        "avgdiff":  [0.5, -0.5, 0.5, -0.5]
    }

    def __init__(self, rtype, iat, rk=0.0, rstwt=None, fixed=False):
        self.rtype = rtype
        self.iat   = iat
        self.rk    = rk
        self.rstwt = rstwt if rstwt is not None else self.DEFAULT_RSTWT.get(rtype)
        self.fixed = fixed  # 2D: use axis1 center instead of axis2

    def format_line(self, n, r1, r2, r3, r4, comment=""):
        iat_str = ",".join(str(i) for i in self.iat)
        line  = f"! {n}" + (f" - {comment}" if comment else "") + "\n"
        line += f"&rst iat={iat_str},\n"
        if self.rstwt:
            line += f"     rstwt={','.join(str(x) for x in self.rstwt)},\n"
        line += f"     r1={r1:.3f}, r2={r2:.3f}, r3={r3:.3f}, r4={r4:.3f},\n"
        line += f"     rk2={self.rk}, rk3={self.rk}\n"
        line += "&end\n\n"
        return line


def load_restraints(config_path):
    with open(config_path) as f:
        entries = json.load(f)
    restraints  = []
    comments    = []
    r_overrides = []
    for e in entries:
        restraints.append(Restraint(
            rtype = e["type"],
            iat   = e["iat"],
            rk    = e.get("rk", 0.0),
            rstwt = e.get("rstwt", None),
            fixed = e.get("fixed", False)
        ))
        comments.append(e.get("comment", ""))
        r_overrides.append({k: e[k] for k in ("r1", "r2", "r3", "r4") if k in e})
    return restraints, comments, r_overrides


def compute_nwin(start, stop, step, label):
    span       = stop - start
    nwin_exact = span / step + 1
    nwin       = int(round(nwin_exact))
    if abs(nwin_exact - nwin) > 1e-6:
        last = start + (nwin - 1) * step
        print(f"Warning: {label} stop={stop} not exactly reachable from start={start} step={step}.")
        print(f"  Using {nwin} windows (last center: {last:.3f})")
    return nwin


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate AMBER restraint files for 1D or 2D umbrella sampling. "
            "1D mode (default): scans axis1, outputs whamN/whamN_rst.dat. "
            "2D mode: add --axis2-* args, outputs wham_i_j/wham_i_j_rst.dat. "
            "JSON 'fixed': true → restraint tracks axis1 center in 2D mode. "
            "Per-entry r1/r2/r3/r4 in JSON override the window center for that restraint."
        )
    )
    parser.add_argument("--config",      required=True,        help="JSON file defining the restraints")
    parser.add_argument("--start",       type=float, default=0.0, help="Axis1 first window center (default 0)")
    parser.add_argument("--stop",        type=float, default=0.0, help="Axis1 last window center (default 0)")
    parser.add_argument("--step",        type=float, default=1.0, help="Axis1 step between windows (default 1)")
    parser.add_argument("--axis2-start", type=float, default=None, help="Axis2 first window center (2D mode)")
    parser.add_argument("--axis2-stop",  type=float, default=None, help="Axis2 last window center (2D mode)")
    parser.add_argument("--axis2-step",  type=float, default=None, help="Axis2 step between windows (2D mode)")
    args = parser.parse_args()

    axis2_vals = (args.axis2_start, args.axis2_stop, args.axis2_step)
    mode_2d = all(v is not None for v in axis2_vals)
    if any(v is not None for v in axis2_vals) and not mode_2d:
        parser.error("Provide all three --axis2-start/stop/step for 2D mode, or none for 1D mode.")

    restraints, comments, r_overrides = load_restraints(args.config)

    nwin1 = compute_nwin(args.start, args.stop, args.step, "axis1")
    nwin2 = compute_nwin(args.axis2_start, args.axis2_stop, args.axis2_step, "axis2") if mode_2d else 1

    for i in range(1, nwin1 + 1):
        center1 = args.start + (i - 1) * args.step

        for j in range(1, nwin2 + 1):
            center2 = (args.axis2_start + (j - 1) * args.axis2_step) if mode_2d else None

            if mode_2d:
                dirname = f"wham_{i}_{j}"
                outfile = os.path.join(dirname, f"wham_{i}_{j}_rst.dat")
            else:
                dirname = f"wham_{i}"
                outfile = os.path.join(dirname, f"wham_{i}_rst.dat")

            os.makedirs(dirname, exist_ok=True)

            with open(outfile, "w") as f:
                for n, (r, c, rov) in enumerate(zip(restraints, comments, r_overrides), 1):
                    center = center1 if (not mode_2d or r.fixed) else center2
                    _r1 = rov.get("r1", -500.0)
                    _r2 = rov.get("r2",  center)
                    _r3 = rov.get("r3",  center)
                    _r4 = rov.get("r4",  500.0)
                    f.write(r.format_line(n, _r1, _r2, _r3, _r4, comment=c))

    total = nwin1 * nwin2
    print(f"Generated {total} restraint file(s) ({'2D' if mode_2d else '1D'} mode)")
    if mode_2d:
        print(f"  Grid: {nwin1} x {nwin2} = {total} windows  (wham_i_j/)")
    else:
        last_center = args.start + (nwin1 - 1) * args.step
        print(f"  wham_1/wham_1_rst.dat  center={args.start:.3f}")
        if nwin1 > 1:
            print(f"  wham_{nwin1}/wham_{nwin1}_rst.dat  center={last_center:.3f}")


if __name__ == "__main__":
    main()
