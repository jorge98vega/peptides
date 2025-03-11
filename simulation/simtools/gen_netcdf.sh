#!/bin/bash

# --------------------------------------------------------
# Descripción:
# Este script descomprime los archivos .coord.gz, genera 
# un archivo de entrada para cpptraj y calcula las trayectorias 
# de simulación, centrando las moléculas y exportando el resultado 
# a un archivo NetCDF.
# 
# Uso:
# 1. Define las variables MOL, DIR y RUN.
# 2. Ejecuta el script.
# --------------------------------------------------------

# Definir variables
MOL=4t10s_run01         # Nombre del sistema
DIR=prod_0              # Directorio de simulación
RUN=prod                # Nombre de la simulación

# Descomprimir archivos .coord.gz
gunzip ${DIR}/${MOL}_${RUN}_*.coord.gz

# Inicializar contador
j=1

# Crear archivo de entrada para cpptraj
while [[ $j -le 500 ]]
do
    echo "trajin ${DIR}/${MOL}_${RUN}_${j}.coord " >> input  # Añade cada archivo de coordenadas a la entrada
    j=$(( j + 1 ))
done

# Comandos para centrar y visualizar moléculas
echo "center :1-320" >> input  # Centra las moléculas seleccionadas (residuos 1-320)
echo "image" >> input          # Aplica la imagen para evitar moléculas fuera del rango
echo "trajout ${DIR}/${MOL}_MD.nc netcdf" >> input  # Exporta las trayectorias en formato NetCDF

# Ejecutar cpptraj
cpptraj ${DIR}/${MOL}.top input  # Ejecuta cpptraj con el archivo de entrada generado

# Eliminar archivo de entrada
rm input
