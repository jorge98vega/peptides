#!/usr/bin/env python3
import os
import argparse

class Restraint:
    DEFAULT_RSTWT = {
        "distance": None,
        "angle": None,
        "diff": [1.0, -1.0],
        "avgdiff": [0.5, -0.5, 0.5, -0.5]
    }

    def __init__(self, rtype, iat, rk=0.0, rstwt=None):
        """
        rtype: tipo ('distance', 'angle', 'diff', 'avgdiff')
        iat: lista de índices de átomos (enteros)
        rk: constante de fuerza (se usa como rk2 y rk3)
        rstwt: lista de pesos (floats) o None para usar el valor por defecto
        """
        self.rtype = rtype
        self.iat = iat
        self.rk = rk
        self.rstwt = rstwt if rstwt is not None else self.DEFAULT_RSTWT.get(rtype)

    def format_line(self, n, r1, r2, r3, r4):
        """Devuelve el restraint en formato AMBER (&rst ... /)"""
        iat_str = ",".join(str(i) for i in self.iat)
        line = f"! {n} - {self.rtype}\n"
        line += f"&rst iat={iat_str},\n"
        if self.rstwt:
            rstwt_str = ",".join(str(x) for x in self.rstwt)
            line += f"     rstwt={rstwt_str}\n"
        line += f"     r1={r1:.3f}, r2={r2:.3f}, r3={r3:.3f}, r4={r4:.3f},\n"
        line += f"     rk2={self.rk}, rk3={self.rk}\n"
        line += "&end\n\n"
        return line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=float, required=True, help="Valor inicial del centro (r2)")
    parser.add_argument("--stop", type=float, required=True, help="Valor final del centro (r2)")
    parser.add_argument("--step", type=float, required=True, help="Incremento por ventana")
    args = parser.parse_args()

    # === Definir restraints aquí ===
    restraints = [
        Restraint("diff", [553, 550, 553, 468], rk=400.0), # d(27HZ3-27NZ) - d(27HZ3-23NZ)
	Restraint("distance", [553, 550], rk=0.0), # d(27HZ3-27NZ)
        Restraint("distance", [553, 468], rk=0.0), # d(27HZ3-23NZ)
        Restraint("distance", [550, 468], rk=0.0), # d(27NZ-23NZ)
        Restraint("angle", [550, 553, 468], rk=0.0), # a(27NZ-27HZ3-23NZ)
        Restraint("distance", [550, 1314], rk=0.0), # d(27NZ-65Cl)
        Restraint("distance", [468, 1314], rk=0.0) # d(23NZ-65Cl)
    ]

    # Calcular número de ventanas
    span = args.stop - args.start
    nwin_exact = span/args.step + 1
    nwin = int(round(nwin_exact)) 

    if abs(nwin_exact - nwin) > 1e-6:
        last_center = args.start + (nwin-1) * args.step
        print(f"⚠️  Aviso: el valor final {args.stop} no coincide exactamente con los pasos desde {args.start} con step {args.step}.")
        print(f"   Se usará el número de ventanas más cercano: {nwin} (valor final {last_center:.3f})")

    # === Bucle de ventanas ===
    for i in range(1, nwin+1):
        b = args.start + (i-1) * args.step
        if i == 1:
            first_center = b
        if i == nwin:
            last_center = b
        r1, r2, r3, r4 = -500.0, b, b, 500.0

        dirname = f"wham{i}"
        os.makedirs(dirname, exist_ok=True)
        outfile = os.path.join(dirname, f"wham{i}_rst.dat")

        with open(outfile, "w") as f:
            for n, r in enumerate(restraints, 1):
                f.write(r.format_line(n, r1, r2, r3, r4))

    # Salida limpia
    print(f"✅ Generados  {nwin} archivos de restraints")
    print(f"   wham1/wham1_rst.dat con centro={first_center:.3f}")
    if nwin > 2:
        print("   ...")
    if nwin > 1:
        print(f"   wham{nwin}/wham{nwin}_rst.dat con centro={last_center:.3f}")


if __name__ == "__main__":
    main()

