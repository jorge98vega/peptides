"""
Este script limpia un archivo PDB eliminando información redundante y asegurando que los residuos estén numerados correctamente. También inserta líneas TER después de cada anillo y al cambiar de residuo.

Uso:
Ejecuta el script pasando el archivo PDB de entrada y generará un nuevo archivo PDB limpio:

python pdbcleaner.py

El archivo de entrada y salida están definidos en pdbfile y newfile.
"""

import numpy as np
import re

# Archivos de entrada y salida
pdbfile = "model_building/run/4t8sX_remove.pdb"
newfile = "model_building/run/4t8sX_preleap.pdb"

# Parámetros del sistema
Nrings = 32  # Número total de anillos
Nres = 8     # Número de residuos por anillo
Natoms = 166 # Número de átomos por anillo
Ntotal = Nrings * Natoms  # Número total de átomos

def clean_pdb():
    """Lee el PDB, limpia los residuos y reescribe el archivo con una estructura correcta."""
    
    names = []       # Nombres de los átomos
    resnames = []    # Nombres de los residuos
    resids = []      # Identificadores de los residuos
    positions = []   # Coordenadas atómicas
    
    # Expresión regular para extraer información del PDB
    regex = re.compile(r"\s*([^\W\d]+\d*-?)\s+(\w+-?)\s*[^\W\d]*\s*(\w+)\s+(-?\d+\.\d+\s+-?\d+\.\d+\s+-?\d+\.\d+)")

    # Leer el archivo PDB
    resid = 0
    previous_resid = ""

    with open(pdbfile, "r") as file:
        for line in file:
            match = regex.match(line)
            if match:
                atom_name, res_name, current_resid, coords = match.groups()
                
                # Numerar residuos correctamente
                if current_resid != previous_resid:
                    previous_resid = current_resid
                    resid += 1
                
                names.append(atom_name)
                resnames.append(res_name)
                resids.append(resid)
                positions.append(np.array(coords.split(), dtype=float))

    # Guardar nuevo PDB limpio
    with open(newfile, "w") as file:
        file.write("\n")
        write_pdb(file, names, resnames, resids, np.array(positions))
        file.write("END   \n")

def write_pdb(file, names, resnames, resids, positions):
    """Escribe el archivo PDB asegurando la estructura correcta."""
    
    resids.append(0)  # Dummy para manejar `TER`
    
    for i, (name, resname, resid, pos) in enumerate(zip(names, resnames, resids, positions)):
        atid = i + 1  # ID del átomo
        
        # Escribir línea de átomo en formato PDB
        file.write(f"ATOM  {atid:>5}  {name:<4} {resname:<3} {resid:>4}    ")
        file.write("".join(f"{x:8.3f}" for x in pos) + "  0.00  0.00\n")
        
        # Insertar `TER` en los límites de anillos o cambios de residuo
        if i < Ntotal:
            if (i + 1) % Natoms == 0:
                file.write("TER   \n")
        else:
            if resid != resids[i + 1]:
                file.write("TER   \n")

# Ejecutar la limpieza del PDB
clean_pdb()
