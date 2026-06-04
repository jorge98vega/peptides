#!/usr/bin/env python3
import os
import argparse
import re

class Restraint:
    DEFAULT_RSTWT = {
        "distance": None,
        "angle": None,
        "diff": [1.0, -1.0],
        "avgdiff": [0.5, -0.5, 0.5, -0.5]
    }

    def __init__(self, rtype, iat, rk=0.0, rstwt=None, fixed=False):
        """
        rtype: tipo ('distance', 'angle', 'diff', 'avgdiff')
        iat: lista de índices de átomos (enteros)
        rk: constante de fuerza (se usa como rk = rk2 = rk3)
        rstwt: lista de pesos (floats) o None para usar el valor por defecto
        fixed: bool, True si la restraint se mantiene fija y usa fixedcenter
        """
        self.rtype = rtype
        self.iat = iat
        self.rk = rk
        self.rstwt = rstwt if rstwt is not None else self.DEFAULT_RSTWT.get(rtype)
        self.fixed = fixed

    def format_line(self, n, center, r1=-500.0, r4=500.0):
        """Devuelve el restraint en formato AMBER (&rst ... /)"""
        iat_str = ",".join(str(i) for i in self.iat)
        line = f"! {n} - {self.rtype}\n"
        line += f"&rst iat={iat_str},\n"
        if self.rstwt:
            rstwt_str = ",".join(str(x) for x in self.rstwt)
            line += f"     rstwt={rstwt_str}\n"
        line += f"     r1={r1:.3f}, r2={center:.3f}, r3={center:.3f}, r4={r4:.3f},\n"
        line += f"     rk2={self.rk}, rk3={self.rk}\n"
        line += "&end\n\n"
        return line


def parse_fixedindex(fixedindex_str):
    """
    Convierte un string tipo 'i=20' o 'j=15' en ('i', 20)
    """
    match = re.match(r"([ij])=(\d+)", fixedindex_str.replace(" ", ""))
    if not match:
        raise ValueError("El parámetro --fixedindex debe tener formato i=N o j=N")
    axis, value = match.groups()
    return axis, int(value)


def main():
    parser = argparse.ArgumentParser(description="Genera restraints para simulaciones WHAM 2D")
    parser.add_argument("--start", type=float, required=True, help="Valor inicial del centro variable")
    parser.add_argument("--stop", type=float, required=True, help="Valor final del centro variable")
    parser.add_argument("--step", type=float, required=True, help="Incremento por ventana")
    parser.add_argument("--fixedcenter", type=float, required=True, help="Centro de las coordenadas fijas")
    parser.add_argument("--fixedindex", type=str, required=True, help="Índice de coordenada fija: formato 'i=20' o 'j=15'")
    args = parser.parse_args()

    # === Definir restraints aquí ===
    restraints = [
        Restraint("diff", [553, 550, 553, 468], rk=400.0, fixed=True), # d(27HZ3-27NZ) - d(27HZ3-23NZ)
        Restraint("diff", [550, 1314, 468, 1314], rk=400.0, fixed=False), # d(27NZ-65Cl) - d(23NZ-65Cl)
	Restraint("distance", [553, 550], rk=0.0), # d(27HZ3-27NZ)
        Restraint("distance", [553, 468], rk=0.0), # d(27HZ3-23NZ)
        Restraint("distance", [550, 468], rk=0.0), # d(27NZ-23NZ)
        Restraint("angle", [550, 553, 468], rk=0.0), # a(27NZ-27HZ3-23NZ)
        Restraint("distance", [550, 1314], rk=0.0), # d(27NZ-65Cl)
        Restraint("distance", [468, 1314], rk=0.0) # d(23NZ-65Cl)
    ]

    axis_fixed, idx_fixed = parse_fixedindex(args.fixedindex)
    axis_var = "j" if axis_fixed == "i" else "i"

    # Calcular número de ventanas
    span = args.stop - args.start
    nwin_exact = span/args.step + 1
    nwin = int(round(nwin_exact)) 

    if abs(nwin_exact - nwin) > 1e-6:
        last_center = args.start + (nwin-1) * args.step
        print(f"⚠️  Aviso: el valor final {args.stop} no coincide exactamente con los pasos desde {args.start} con step {args.step}.")
        print(f"   Se usará el número de ventanas más cercano: {nwin} (valor final {last_center:.3f})")

    # === Bucle de ventanas ===
    for iwin in range(1, nwin+1):
        varcenter = args.start + (iwin-1) * args.step
        if iwin == 1:
            first_center = varcenter
        if iwin == nwin:
            last_center = varcenter

        # Asignar nombres coherentes con wham_i_j
        if axis_fixed == "i":
            i, j = idx_fixed, iwin
        else:
            i, j = iwin, idx_fixed

        dirname = f"wham_{i}_{j}"
        os.makedirs(dirname, exist_ok=True)
        outfile = os.path.join(dirname, f"wham_{i}_{j}_rst.dat")

        with open(outfile, "w") as f:
            for n, r in enumerate(restraints, 1):
                center = args.fixedcenter if r.fixed else varcenter
                f.write(r.format_line(n, center))

    # Salida limpia
    print(f"✅ Generados  {nwin} archivos de restraints")
    fristfilename = f"wham_{1 if axis_fixed=='j' else idx_fixed}_{1 if axis_fixed=='i' else idx_fixed}"
    print(f"   {fristfilename}/{fristfilename}_rst.dat con centro (variable) {first_center:.3f}")
    if nwin > 2:
        print("   ...")
    if nwin > 1:
        lastfilename = f"wham_{nwin if axis_fixed=='j' else idx_fixed}_{nwin if axis_fixed=='i' else idx_fixed}"
        print(f"   {lastfilename}/{lastfilename}_rst.dat con centro (variable) {last_center:.3f}")


if __name__ == "__main__":
    main()

