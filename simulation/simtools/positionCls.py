"""
Este script procesa un archivo PDB para:
    Mantener la estructura y numeración de residuos correcta.
    Detectar residuos LYS y almacenar posiciones de átomos que coincidan con \wZ\d?.
    Ajustar la posición de los átomos Cl- en función de la posición promedio de los átomos HZ de la misma LYS.

Uso:
    Ejecutar con:
    python positionCls.py

El archivo de entrada (pdbfile) se procesará y generará un nuevo archivo limpio (newfile).
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

def process_pdb():
    """Lee el PDB, limpia los residuos y ajusta posiciones de Cl- según la LYS correspondiente."""
    
    names = []       # Nombres de los átomos
    resnames = []    # Nombres de los residuos
    resids = []      # Identificadores de los residuos
    positions = []   # Coordenadas atómicas
    zpos = []        # Posiciones específicas para LYS
    
    # Expresión regular para extraer información del PDB
    regex = re.compile(r"\s*([^\W\d]+\d*-?)\s+(\w+-?)\s*[^\W\d]*\s*(\w+)\s+(-?\d+\.\d+\s+-?\d+\.\d+\s+-?\d+\.\d+)")

    resid = 0
    clcount = 0
    previous_resid = ""

    with open(pdbfile, "r") as file:
        for line in file:
            match = regex.match(line)
            if match:
                atom_name, res_name, current_resid, coords = match.groups()
                coords = np.array(coords.split(), dtype=float)

                # Guardar posiciones de átomos en LYS con patrón \wZ\d?
                if res_name == "LYS" and re.search(r"\wZ\d?", atom_name):
                    zpos.append(coords)

                # Numerar residuos correctamente
                if current_resid != previous_resid:
                    previous_resid = current_resid
                    resid += 1
                
                names.append(atom_name)
                resnames.append(res_name)
                resids.append(resid)

                # Ajuste especial para Cl-
                if res_name == "Cl-":
                    clcount += 1
                    NZpos = np.array(zpos[12 * (clcount - 1)][:3])
                    HZav = np.mean([zpos[12 * (clcount - 1) + 3 * hz][:3] for hz in range(1, 4)], axis=0)
                    clpos = NZpos + (HZav - NZpos) * 10.0
                    positions.append(clpos)
                else:
                    positions.append(coords)

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

# Ejecutar el procesamiento del PDB
process_pdb()
