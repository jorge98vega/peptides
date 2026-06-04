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

    def __init__(self, rtype, iat, rk=0.0, rstwt=None):
        self.rtype = rtype
        self.iat   = iat
        self.rk    = rk
        self.rstwt = rstwt if rstwt is not None else self.DEFAULT_RSTWT.get(rtype)

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
    r_overrides = []  # per-entry r1/r2/r3/r4; if present, overrides the window center
    for e in entries:
        restraints.append(Restraint(
            rtype = e["type"],
            iat   = e["iat"],
            rk    = e.get("rk", 0.0),
            rstwt = e.get("rstwt", None)
        ))
        comments.append(e.get("comment", ""))
        r_overrides.append({k: e[k] for k in ("r1", "r2", "r3", "r4") if k in e})
    return restraints, comments, r_overrides


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate AMBER restraint files for WHAM umbrella sampling. "
            "Each window writes whamN/whamN_rst.dat with r2=r3=window_center. "
            "Per-entry r1/r2/r3/r4 in the JSON override the window center for that restraint "
            "(useful for fixed or upper/lower-bound restraints in the same file)."
        )
    )
    parser.add_argument("--config", required=True, help="JSON file defining the restraints")
    parser.add_argument("--start",  type=float, default=0.0, help="First window center (default 0)")
    parser.add_argument("--stop",   type=float, default=0.0, help="Last window center (default 0)")
    parser.add_argument("--step",   type=float, default=1.0, help="Step between window centers (default 1)")
    args = parser.parse_args()

    restraints, comments, r_overrides = load_restraints(args.config)

    span       = args.stop - args.start
    nwin_exact = span / args.step + 1
    nwin       = int(round(nwin_exact))

    if abs(nwin_exact - nwin) > 1e-6:
        last_center = args.start + (nwin - 1) * args.step
        print(f"Warning: {args.stop} is not exactly reachable from {args.start} with step {args.step}.")
        print(f"  Using {nwin} windows (last center: {last_center:.3f})")

    for i in range(1, nwin + 1):
        b = args.start + (i - 1) * args.step
        r1_def, r2_def, r3_def, r4_def = -500.0, b, b, 500.0

        dirname = f"wham{i}"
        os.makedirs(dirname, exist_ok=True)
        outfile = os.path.join(dirname, f"wham{i}_rst.dat")

        with open(outfile, "w") as f:
            for n, (r, c, rov) in enumerate(zip(restraints, comments, r_overrides), 1):
                _r1 = rov.get("r1", r1_def)
                _r2 = rov.get("r2", r2_def)
                _r3 = rov.get("r3", r3_def)
                _r4 = rov.get("r4", r4_def)
                f.write(r.format_line(n, _r1, _r2, _r3, _r4, comment=c))

    first_center = args.start
    last_center  = args.start + (nwin - 1) * args.step
    print(f"Generated {nwin} restraint file(s)")
    print(f"  wham1/wham1_rst.dat  center={first_center:.3f}")
    if nwin > 2:
        print("  ...")
    if nwin > 1:
        print(f"  wham{nwin}/wham{nwin}_rst.dat  center={last_center:.3f}")


if __name__ == "__main__":
    main()
