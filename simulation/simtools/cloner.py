"""
Script para clonar y modificar un archivo PDB.

Este script lee un archivo PDB, extrae información relevante sobre los átomos y residuos, 
y genera una nueva estructura clonada con transformaciones específicas (traslación y rotación).

Uso:
    Simplemente ejecutar el script asegurándose de que el archivo de entrada PDB exista.

Dependencias:
    - numpy
    - re
"""

import numpy as np
import re

# Parámetros del sistema
pdbfile = "model_building/run/4t8sX_remove.pdb"  # Archivo de entrada
newfile = "model_building/run/4t8sX_preleap.pdb"  # Archivo de salida

Nrings = 32   # Número de anillos a clonar
Nres = 8      # Número de residuos por anillo
Natoms = 166  # Número de átomos en un anillo
Ntotal = Nrings * Natoms  # Número total de átomos en el sistema

# Parámetros de clonación (traslaciones y ángulos en grados)
ts = np.array([
    [0.0,  0.0,  0.0],
    [22.0, 0.0,  0.0],
    [22.0, 22.0, 0.0],
    [0.0,  22.0, 0.0]
])

as_angles = np.array([10.0, 10.0, 10.0, 10.0])  # Ángulos en grados


def rotate(pos, center, alpha):
    """
    Rota un punto `pos` en torno a un centro `center` un ángulo `alpha` (radianes) alrededor del eje Z.
    """
    alpha_rad = np.radians(alpha)  # Convertir a radianes
    rotmat = np.array([
        [np.cos(alpha_rad), -np.sin(alpha_rad), 0],
        [np.sin(alpha_rad),  np.cos(alpha_rad), 0],
        [0,                 0,                 1]
    ])
    return np.dot(rotmat, pos - center) + center


def clon(file, names, resnames, resids, pos, com, t, alpha, n):
    """
    Clona los átomos aplicando transformaciones y escribe en el archivo PDB.
    """
    for ring in range(Nrings):
        for atom in range(Natoms):
            index = ring * Natoms + atom
            atid = (n - 1) * Ntotal + index + 1  # Ajuste de índice
            resid = (n - 1) * Nrings * Nres + resids[index]

            # Aplicar transformación
            rotpos = rotate(pos[index], com, alpha)
            newpos = rotpos + t

            # Escribir en el archivo PDB
            file.write(f"ATOM  {atid:5d}  {names[index]:<4} {resnames[index]:<3} {resid:4d}    ")
            file.write(f"{newpos[0]:8.3f}{newpos[1]:8.3f}{newpos[2]:8.3f}  0.00  0.00\n")

        file.write("TER   \n")


def main():
    """
    Función principal: lee el PDB, extrae datos, clona y escribe el nuevo archivo.
    """
    names, resnames, resids = [], [], []
    pos = np.zeros((Ntotal, 3))
    com = np.zeros(3)

    # Expresión regular para leer átomos en un archivo PDB
    pdb_regex = re.compile(r"\s*ATOM\s+\d+\s+(\S+)\s+(\S+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")

    # Leer el archivo PDB
    with open(pdbfile, "r") as file:
        i = 0
        for line in file:
            match = pdb_regex.match(line)
            if match:
                names.append(match.group(1))
                resnames.append(match.group(2))
                resids.append(int(match.group(3)))
                pos[i] = [float(match.group(4)), float(match.group(5)), float(match.group(6))]
                com += pos[i]
                i += 1
                if i >= Ntotal:
                    break

    # Calcular centro de masa
    com /= Ntotal
    resids = np.array(resids)

    # Escribir el nuevo archivo PDB con los clones
    with open(newfile, "w") as file:
        file.write("\n")
        for n in range(len(ts)):
            clon(file, names, resnames, resids, pos, com, ts[n], as_angles[n], n + 1)
        file.write("END   \n")


if __name__ == "__main__":
    main()
