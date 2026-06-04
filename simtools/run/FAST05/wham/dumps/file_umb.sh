#!/bin/bash

# Descripción:
# Este script procesa archivos de salida de simulaciones WHAM, extrayendo datos relevantes
# y generando archivos necesarios para realizar un análisis de muestreo con el método WHAM.

# Elimina el directorio umbrella_files si existe y lo vuelve a crear
rm -r umbrella_files
mkdir umbrella_files

# Bucle sobre los pasos (steps) de 1 a 28
for i in {1..28..1} 
do
  # Calcula el centro del potencial para cada paso
  # El valor b varía de 2.650 a 1.250 en decrementos de 0.050 por paso
  b=$(echo "scale=3; 2.650-($i*0.050)" | bc) 

  # Extrae las dos primeras columnas del archivo de datos, conservando solo las últimas 1500 líneas
  awk '{print $1,$2}' wham_rst_${i}.dump | tail -1500 > umbrella_files/mc_${i}.out

  # Agrega una línea a meta.dat con el archivo de salida, el centro del potencial y la constante de fuerza
  # El valor 800 es el doble del rk en rst.dat
  echo mc_${i}.out ${b} 800 >> umbrella_files/meta.dat
done

# Cambia al directorio umbrella_files
cd umbrella_files

# Ejecuta el análisis WHAM con los siguientes parámetros:
# hist_min = 1.25, hist_max = 2.6, num_bins = 50, tolerance = 0.0001, temperature = 300,
# periodic = 0 (no periódico), metafile = meta.dat, outfile = wham.out
/home/jorge/bin/wham/wham/wham 1.25 2.6 50 0.0001 300 0 meta.dat wham.out

# Regresa al directorio principal
cd ..
