#!/usr/bin/env python3
"""
Este script:
    Lee un archivo PDB (pdbfile).
    Sustituye un residuo (oldresname) por otro, tomando la estructura del nuevo residuo desde otro archivo PDB (subspdb).
    Ajusta las coordenadas sumando la posición del viejo residuo con las del nuevo.
    Escribe el nuevo archivo PDB (newfile).

Uso:
    Ejecutar con:
    python substitute_res.py Cl- TFA.pdb

    Esto sustituirá todos los residuos Cl- por los definidos en TFA.pdb.
"""

import numpy as np
import re
import sys

# Archivos
pdbfile = "model_building/run/4t8sX_remove.pdb"
newfile = "model_building/run/4t8sX_preleap.pdb"

# Parámetros del sistema
Nrings = 32  # Número total de anillos
Natoms = 166 # Número de átomos por anillo
Ntotal = Nrings * Natoms  # Número total de átomos


def read_pdb(filename):
    """Lee un archivo PDB y extrae nombres, residuos, IDs y coordenadas."""
    names, resnames, resids, positions = [], [], [], []
    
    regex = re.compile(r"\s*([^\W\d]+\d*-?)\s+(\w+-?)\s*[^\W\d]*\s*(\w+)\s+(-?\d+\.\d+\s+-?\d+\.\d+\s+-?\d+\.\d+)")

    resid = 0
    previous_resid = ""

    with open(filename, "r") as file:
        for line in file:
            match = regex.match(line)
            if match:
                atom_name, res_name, current_resid, coords = match.groups()
                coords = np.array(coords.split(), dtype=float)

                if current_resid != previous_resid:
                    previous_resid = current_resid
                    resid += 1
                
                names.append(atom_name)
                resnames.append(res_name)
                resids.append(resid)
                positions.append(coords)

    return names, resnames, resids, np.array(positions)


def write_pdb(file, names, resnames, resids, positions):
    """Escribe el archivo PDB con los residuos sustituidos correctamente."""
    resids.append(0)  # Dummy para manejar `TER`

    for i, (name, resname, resid, pos) in enumerate(zip(names, resnames, resids, positions)):
        atid = i + 1

        file.write(f"ATOM  {atid:>5}  {name:<4} {resname:<3} {resid:>4}    ")
        file.write("".join(f"{x:8.3f}" for x in pos) + "  0.00  0.00\n")

        # Insertar TER en los límites de anillos o cambios de residuo
        if i < Ntotal:
            if (i + 1) % Natoms == 0:
                file.write("TER   \n")
        else:
            if resid != resids[i + 1]:
                file.write("TER   \n")


def substitute_residue(oldresname, subspdb):
    """Sustituye el residuo `oldresname` por la estructura de `subspdb`."""
    
    # Leer los archivos PDB
    names, resnames, resids, positions = read_pdb(pdbfile)
    subs_names, subs_resnames, subs_resids, subs_positions = read_pdb(subspdb)

    new_names, new_resnames, new_resids, new_positions = [], [], [], []
    
    lastsubs = 0
    subsatoms = 0

    resids.append(0)  # Dummy para `TER`

    for i, (name, resname, resid, pos) in enumerate(zip(names, resnames, resids, positions)):
        if resname == oldresname:
            if resid == lastsubs:
                continue  # Evitar duplicados

            lastsubs = resid
            subsatoms += len(subs_names) - 1

            for j, (sub_name, sub_resname, sub_resid, sub_pos) in enumerate(zip(subs_names, subs_resnames, subs_resids, subs_positions)):
                new_names.append(sub_name)
                new_resnames.append(sub_resname)
                new_resids.append(resid + sub_resid - 1)
                new_positions.append(pos + sub_pos)

        else:
            new_names.append(name)
            new_resnames.append(resname)
            new_resids.append(resid)
            new_positions.append(pos)

    # Guardar el nuevo archivo PDB
    with open(newfile, "w") as file:
        file.write("\n")
        write_pdb(file, new_names, new_resnames, new_resids, np.array(new_positions))
        file.write("END   \n")


# Ejecutar con argumentos
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python substitute_res.py <oldresname> <subspdb>")
        sys.exit(1)

    oldresname = sys.argv[1]
    subspdb = sys.argv[2]
    
    substitute_residue(oldresname, subspdb)
