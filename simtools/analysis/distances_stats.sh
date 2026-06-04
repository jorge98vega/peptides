#!/bin/bash
# Script para extraer distancias y calcular estadísticas (media y desviación estándar) de múltiples archivos

MOL=4tubes_run01      # Nombre del modelo o molécula
DIR=prod_dist         # Directorio de los archivos de salida
RUN=prod              # Nombre de la ejecución o run

# Crear archivos de salida vacíos
> ${DIR}/${MOL}_distances.dat  # Archivo para almacenar las distancias
> ${DIR}/${MOL}_stats.dat     # Archivo para almacenar las estadísticas

INI=1  # Primer archivo
FIN=50 # Último archivo
COLS=( 7 8 1 9 10 2 11 12 3 13 14 4 15 16 5 17 18 6 ) # Columnas a considerar

# Extraer las distancias de cada archivo .out y almacenarlas en distances.dat
i=$INI
while [[ $i -le $FIN ]]
do
    # Extrae las columnas del archivo de distancias y las agrega al archivo de salida
    awk '{for(i=2; i<=NF; ++i) printf $i" "; print ""}' ${DIR}/${MOL}_${RUN}_${i}_rst.out >> ${DIR}/${MOL}_distances.dat
    i=$(( i + 1 ))
done

# Calcular estadísticas para cada columna definida en COLS
for j in "${COLS[@]}"
do
    # Calcular la media y desviación estándar para cada columna seleccionada
    awk -v N=$j '{ sum += $N; sumsq += ($N)^2} END { if (NR > 0) printf "%f %f \n", sum/NR, sqrt((sumsq - sum^2/NR)/NR) }' ${DIR}/${MOL}_distances.dat >> ${DIR}/${MOL}_stats.dat
done
