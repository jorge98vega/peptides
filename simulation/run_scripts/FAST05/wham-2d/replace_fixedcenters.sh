#!/bin/bash
#
# Uso: ./replace_fixedcenters.sh centers.dat
# El archivo centers.dat debe tener formato: iwindow center otronumero
# Supone 25 ventanas de c1: c1 va de -1.2 a 1.2 en pasos de 0.1
# Para cada c1, c2 va de (c1-1.2) a (c1+1.2) en pasos de 0.1 (25 ventanas)

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo_centers.dat>"
    exit 1
fi

centers_file="$1"
if [ ! -f "$centers_file" ]; then
    echo "❌ No se encontró el archivo $centers_file"
    exit 1
fi

# Parámetros de c1
c1_start=-1.2
c1_step=0.1
nwin=25

while read -r iwindow center _; do
    dir="wham_${iwindow}_1"
    file="${dir}/${dir}_rst.dat"

    if [ -f "$file" ]; then
        # Calcular valor de c1 para esta ventana
        c1_val=$(awk -v i="$iwindow" -v start="$c1_start" -v step="$c1_step" 'BEGIN {printf "%.1f", start + (i - 1) * step}')

        # Redondear center al primer decimal y mostrar con tres decimales
        rounded=$(awk -v val="$center" 'BEGIN {printf "%.3f", sprintf("%.1f", val)}')

        # Calcular ventana correspondiente de c2 (dentro del rango [c1-1.2, c1+1.2])
        c2_min=$(awk -v c1="$c1_val" 'BEGIN {print -2.4}')
        c2_max=$(awk -v c1="$c1_val" 'BEGIN {print 2.4}')
        c2_win=$(awk -v c2="$rounded" -v c2min="$c2_min" 'BEGIN {printf "%d", int(((c2 - c2min) / 0.1) + 1.0001)}')

        # Sustituir el marcador 7.777 por el valor redondeado
        sed -i "s/7\.777/${rounded}/g" "$file"

        # Salida
        echo "Ventana c1 ${iwindow} (c1=${c1_val}): 7.777 → ${rounded} (corresponde a ventana c2 ${c2_win})"
    else
        echo "No se encontró $file (ventana $iwindow)"
    fi
done < "$centers_file"

