#!/bin/bash
# Script para centrar y ajustar la imagen de un solo frame (RST) usando CPPTRAJ

MOL=4t10s_run01  # Nombre del modelo o molécula
DIR=prod_0       # Directorio de los archivos de la simulación
RUN=prod         # Nombre de la ejecución o run

j=1  # Número del frame (por ejemplo, el primer frame)

# Crear archivo de entrada para cpptraj
echo "trajin ${DIR}/${MOL}_${RUN}_${j}.rst" >> input   # Archivo de entrada del frame
echo "center :1-320" >> input                            # Centra los átomos del rango :1-320
echo "image" >> input                                    # Ajusta la imagen de las moléculas
echo "trajout ${DIR}/${MOL}_${RUN}_${j}_recenter.rst" >> input  # Archivo de salida (frame recenterizado)

# Ejecutar cpptraj para procesar el archivo
cpptraj ${DIR}/${MOL}.top input

# Eliminar archivo temporal de entrada
rm input
